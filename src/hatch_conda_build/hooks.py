from hatchling.plugin import hookimpl

from hatch_conda_build.plugin import CondaBuilder


@hookimpl
def hatch_register_builder():
    return CondaBuilder
