import pathlib


def _get_driver(s: str) -> pathlib.Path:
    p = pathlib.Path(s)
    if not p.exists():
        raise FileNotFoundError("Driver '{}' does not exist".format(s))

    return p


def get_avrlibc_r2537() -> pathlib.Path:
    return _get_driver('./runner/runner-avrlibc-r2537')


def get_tcmalloc_2_6_1() -> pathlib.Path:
    return _get_driver('./runner/runner-tcmalloc-2.6.1')


def get_jemalloc_5_0_1() -> pathlib.Path:
    return _get_driver('./runner/runner-jemalloc-5.0.1')


def get_dlmalloc_2_8_6() -> pathlib.Path:
    return _get_driver('./runner/runner-dlmalloc-2.8.6')


def get_default() -> pathlib.Path:
    return _get_driver('./runner/runner')
