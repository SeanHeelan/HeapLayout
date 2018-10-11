#!/usr/bin/env python3

"""Search for a solution to an ordering constraint over two dynamically
allocated buffers.

This version hardcodes the source and destination sequences for the search. The
source buffer is the first buffer allocated by xml_parse() as part of the PHP
XML OOB read bug, while the destination buffer is the 3rd buffer allocated by
imagecreatetruecolor(1, 1). The read takes place at src_buf + 24 + X, where X
is a directly controllable 32-bit value.

Our goal is to minimise the absolute difference between src_buf and dst_buf.
The files we generate will look as follows:

    <bug related setup>
    ...
    <heap manipulation 1>
    ...
    shrike_record_destination(2);
    imagecreatetruecolor(1, 1);
    shrike_record_source(0);
    xml_parse();

The majority of our work will be the <heap manipulation 1> component. We could
potentially also perform manipulation at <heap manipulation 2>, but this would
only be relevant if the manipulation at the first stage cannot find a solution.
"""

import argparse
import logging
import os
import pathlib
import shutil
import sys

from shrike import php7
from shrike import FragmentStore
from shrike import Template

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
        'fragments', nargs='+',
        help='A list of pickle files mapping fragments to their summaries')
parser.add_argument(
        '-o', '--output', required=True,
        help="The output directory to store results")
parser.add_argument(
        '-p', '--php', required=True,
        help="The PHP binary to use")
parser.add_argument(
        '--template', required=True,
        help="The vulnerability template to use")
parser.add_argument(
        '-j', '--jobs', type=int, default=os.cpu_count(),
        help="The number of concurrent jobs to run")
parser.add_argument(
        '-t', '--time-limit', type=int, default=300,
        help="The maximum run time")
parser.add_argument(
        '--debug', action='store_true', default=False,
        help="Enable debug mode (verbose logging)")
parser.add_argument(
        '--no-delete-candidates', action='store_true', default=False,
        help=(
            "Don't remove the generated candidates. WARNING: Will quickly"
            "produce a very large number of files in the output directory"))
parser.add_argument(
        '--single-process', action='store_true', default=False,
        help="Run analysis in a single process (--jobs is then ignored)")
parser.add_argument(
        '--overwrite-output', action='store_true', default=False,
        help="If the output directory exists then recreate it")
args = parser.parse_args()

if args.debug:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG)

output_dir_path = pathlib.Path(args.output)
if output_dir_path.exists():
    if args.overwrite_output:
        shutil.rmtree(output_dir_path.as_posix())
        os.mkdir(output_dir_path.as_posix())
    else:
        logger.error("Output directory {} exists".format(output_dir_path))
        sys.exit(1)
else:
    os.mkdir(output_dir_path.as_posix())

if args.single_process:
    logger.info("Running a single analysis process")
else:
    logger.info("Utilising {} cores".format(args.jobs))

logger.info("Analysing the PHP binary at {}".format(args.php))
logger.info("Template: {}".format(args.template))
logger.info("Time limit: {}".format(args.time_limit))

fragment_paths = [pathlib.Path(p) for p in args.fragments]
fragment_store = FragmentStore(fragment_paths)
logger.info("{} unique sequences across {} fragments loaded from {}".format(
    fragment_store.num_sequences(), fragment_store.num_fragments(),
    [p.as_posix() for p in fragment_paths]))

template = Template(args.template, fragment_store)
logger.info("Loaded template from {}".format(args.template))
logger.info("Template contains {} stages".format(
    template.num_remaining_stages()))

for size in template.hlm_sizes_in_use():
    fragments = fragment_store.get_fragments_for_size(size)
    if fragments:
        logger.info("{} allocation sequences for size {}".format(
                len(fragments), size))
    else:
        logger.error("No allocation sequence for size {}".format(size))
        sys.exit(1)

    shortest_for_size = fragment_store.get_shortest_fragments_for_size(
            size)
    logger.info(
            ("Shortest sequences for size {} have length {} ("
                "{} alternates)").format(
                    size, shortest_for_size[0][1]._length,
                    len(shortest_for_size)))

orig_path = pathlib.Path(args.template)
shutil.copyfile(args.template, output_dir_path / orig_path.name)

while not template.is_solved():
    if args.single_process:
        success, template = php7.minimise_distance_single_process(
                args.php, template, args.time_limit, args.no_delete_candidates)
    else:
        success, template = php7.minimise_distance(
                args.jobs, args.php, template, args.time_limit,
                args.no_delete_candidates)

    if not success:
        logger.error("Failed to solve stage {}".format(
            template.current_stage()))
        sys.exit(1)

    template.mark_current_stage_as_solved()
    # Zero fill to the same length as the temporary file names. The PHP
    # interpreter performs allocations based on the length of the command line
    # arguments provided to it.
    output_file_name = "{}_solution".format(template.current_stage()).zfill(36)
    stage_result_path = output_dir_path / output_file_name
    template.save_to(stage_result_path)
