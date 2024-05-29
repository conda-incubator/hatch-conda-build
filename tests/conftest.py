import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture(scope="session")
def plugin_dir():
    with TemporaryDirectory() as d:
        directory = Path(d, "plugin")
        shutil.copytree(Path.cwd(), directory, ignore=shutil.ignore_patterns(".git"))

        yield directory.resolve()


@pytest.fixture
def new_project(tmp_path, monkeypatch, plugin_dir):
    def _new_project(
        name: str = "project-a",
        package_name: str = "project_a",
        version: str = "0.1.0",
        dependencies: list[str] = ["requests"],
    ):
        project_dir = tmp_path / name
        project_dir.mkdir()

        project_file = project_dir / "pyproject.toml"
        project_file.write_text(
            f"""\
[build-system]
requires = ["hatchling", "hatch-conda-build @ {plugin_dir.as_uri()}"]
build-backend = "hatchling.build"

[project]
name = "project-a"
version = "0.1.0"
description = "A description"
requires-python = ">=3.8"
dependencies = {json.dumps(dependencies)}

[project.urls]
homepage = "https://example.org"

[tool.hatch.build.targets.conda]
channels = ["conda-forge"]
    """,
            encoding="utf-8",
        )

        package_dir = project_dir / "src" / package_name
        package_dir.mkdir(parents=True)

        package_root = package_dir / "__init__.py"
        package_root.write_text("")

        monkeypatch.chdir(project_dir)

        return project_dir

    return _new_project

