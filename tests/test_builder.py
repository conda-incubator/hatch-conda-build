import pytest
# from hatchling.builders.plugin.interface import IncludedFile
from hatchling.metadata.core import ProjectMetadata

from hatch_conda_build.plugin import CondaBuilder


@pytest.fixture
def conda_builder(new_project):
    hatch_config = {
        "build": {
            "targets": {
                "conda": {"install-name": "project-a"}
            },
        },
    }
    config = {
        "project": {"name": "project-a", "version": "0.1.0"},
        "tool": {
            "hatch": hatch_config,
        },
    }
    project_root = new_project(name="project-a", package_name="project_a", version="0.1.0",
                               dependencies=["requests", "Flask", "build", "art", "pydantic[email]<2"])

    metadata = ProjectMetadata(project_root, None, config=config)

    builder = CondaBuilder(project_root, metadata=metadata)
    return builder


def test_conda_build(conda_builder):
    conda_builder.build_standard(directory=conda_builder.config.directory)
    assert conda_builder
