import logging
import pathlib


def get_logger_name() -> str:
    """Return the name of the logger for this tool"""
    return 'expres'


def get_logger() -> logging.Logger:
    """Return the logger"""

    return logging.getLogger(get_logger_name())


def get_formatter() -> logging.Formatter:
    """Return the formatter"""

    return logging.Formatter(
            ('%(asctime)s %(levelname)-8s %(process)d '
             '%(module)s:%(funcName)s:%(lineno)d %(message)s'),
            datefmt='%Y-%m-%d %H:%M:%S')

def configure_logger(output_dir: pathlib.Path, enable_debug: bool = False):
    """Configure the console and file logger.

    Should only be called once and must be called before the first call to
    get_logger.
    """

    ch = logging.StreamHandler()
    if enable_debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)

    formatter = get_formatter()
    ch.setFormatter(formatter)

    logger = get_logger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    fh = logging.FileHandler(output_dir / 'output.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
