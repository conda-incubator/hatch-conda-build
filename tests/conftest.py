import json
import shutil
from hatchling.metadata.core import ProjectMetadata
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Optional

import pytest


@pytest.fixture(scope="session")
def plugin_dir():
    with TemporaryDirectory() as d:
        directory = Path(d, "plugin")
        shutil.copytree(Path.cwd(), directory, ignore=shutil.ignore_patterns("env"))

        yield directory.resolve()


@pytest.fixture
def project_factory(tmp_path, plugin_dir):
    def _new_project(
        name: str = "project-a",
        package_name: str = "project_a",
        version: str = "0.1.0",
        dependencies: list[str] = ["requests"],
        requires_python: str = ">=3.8",
        more_toml: Optional[str] = None,
    ) -> ProjectMetadata:
        project_dir = tmp_path / name
        project_dir.mkdir()

        toml = dedent(
            f"""\
            [build-system]
            requires = ["hatchling", "hatch-conda-build @ {plugin_dir.as_uri()}"]
            build-backend = "hatchling.build"

            [project]
            name = "{name}"
            version = "{version}"
            description = "A description"
            requires-python = "{requires_python}"
            dependencies = {json.dumps(dependencies)}

            [project.urls]
            homepage = "https://example.org"
            """
        )

        if more_toml is not None:
            toml += more_toml

        project_file = project_dir / "pyproject.toml"
        project_file.write_text(toml, encoding="utf-8")

        package_dir = project_dir / "src" / package_name
        package_dir.mkdir(parents=True)

        package_init = package_dir / "__init__.py"
        package_init.write_text(f"__version__ = '{version}'\n")

        return project_dir

    return _new_project
