import json
import shutil
import sys
import typing
import pathlib
import collections
import tempfile
import subprocess
from deepmerge.merger import Merger
from pathlib import Path
from typing import Optional, List

from hatchling.builders.plugin.interface import BuilderInterface

from hatch_conda_build.config import CondaBuilderConfig

from grayskull.strategy.py_base import merge_setup_toml_metadata
from grayskull.strategy.py_toml import get_all_toml_info
from souschef.recipe import Recipe
from grayskull.config import Configuration
from grayskull.strategy.pypi import extract_requirements, normalize_requirements_list
from grayskull.strategy.pypi import merge_pypi_sdist_metadata


recipe_merger = Merger(
    type_strategies=[(dict, ["merge"]), (list, ["append"])],
    fallback_strategies=["override"],
    type_conflict_strategies=["override"],
)


def normalize_host_packages(packages: typing.List[str]):
    _packages = []
    for package in packages:
        if "hatch-conda-build" in package:
            continue

        if "@" in package:
            package = package.split("@")[0]

        _packages.append(package)
    return _packages


def conda_build(
    meta_config: typing.Dict,
    build_directory: pathlib.Path,
    output_directory: pathlib.Path,
    channels: typing.List[str],
    default_numpy_version: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
):
    conda_meta_filename = build_directory / "meta.yaml"
    with conda_meta_filename.open("w") as f:
        json.dump(meta_config, f)

    command = [
        "conda",
        "build",
        str(build_directory),
        "--output-folder",
        str(output_directory),
        "--override-channels",
    ]

    if extra_args is not None:
        command.extend(extra_args)

    if default_numpy_version is not None:
        command.extend(
            [
                "--numpy",
                default_numpy_version,
            ]
        )

    for channel in channels:
        command += ["--channel", channel]

    subprocess.run(command, check=True, stderr=sys.stderr, stdout=sys.stdout)

    package_name = (
        f"{meta_config['package']['name']}-"
        f"{meta_config['package']['version']}-"
        f"py_{meta_config['build']['number']}.conda"
    )
    return output_directory / "noarch" / package_name


class CondaBuilder(BuilderInterface):
    PLUGIN_NAME = "conda"

    def get_version_api(self) -> typing.Dict:
        return {"standard": self.build_standard}

    def clean(self, directory: str, versions: typing.List[str]):
        builds = Path(directory) / "conda"
        shutil.rmtree(builds)

    def _get_requirements(self):
        """Use grayskull to extract requirements and transform to conda"""
        recipe = Recipe(name=self.metadata.name, version=self.metadata.version)
        config = Configuration(
            name=self.metadata.name,
            version=self.metadata.version,
            from_local_sdist=True,
        )

        # prepare requirements from pyproject.toml
        assert (
            self.metadata.has_project_file() and self.metadata._project_file is not None
        )
        full_metadata = get_all_toml_info(self.metadata._project_file)
        merged = merge_setup_toml_metadata({}, full_metadata)
        merged2 = merge_pypi_sdist_metadata({}, merged, config)

        requirements = extract_requirements(merged2, config, recipe)

        for key in requirements:
            _normalized = normalize_requirements_list(requirements[key], config)
            if key == "host":
                # drop hatch-conda-build
                normalized = normalize_host_packages(_normalized)
            else:
                normalized = _normalized

            requirements[key] = normalized

        return requirements

    def _construct_recipe(self):
        conda_meta = collections.defaultdict(dict)

        conda_meta["package"]["name"] = self.metadata.name
        conda_meta["package"]["version"] = self.metadata.version

        # package
        conda_meta["source"]["path"] = str(self.root)

        # build
        conda_meta["build"] = {
            "number": 0,
            "noarch": "python",
            "script": "{{ PYTHON }} -m pip install --no-build-isolation --no-deps --ignore-installed -vv .",
        }

        # requirements
        conda_meta["requirements"] = self._get_requirements()

        # test
        conda_meta["test"] = {}

        # about
        conda_meta["about"]["home"] = self.metadata.core_raw_metadata.get(
            "urls", {}
        ).get("homepage")
        conda_meta["about"]["summary"] = self.metadata.core_raw_metadata.get(
            "description"
        )

        # merge extra keys and overrides
        extras = self.target_config.get("recipe", {})
        recipe_merger.merge(conda_meta, extras)

        return conda_meta

    def build_standard(self, directory: str, **build_data: typing.Dict) -> str:
        conda_bld = pathlib.Path(directory) / "conda"

        conda_meta = self._construct_recipe()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = pathlib.Path(tmpdir)

            conda_build_filename = conda_build(
                conda_meta,
                build_directory=tmpdir,
                output_directory=conda_bld,
                channels=self.target_config.get("channels", ["conda-forge"]),
                default_numpy_version=self.target_config.get(
                    "default_numpy_version", None
                ),
            )

        return str(conda_build_filename)

    @classmethod
    def get_config_class(cls):
        return CondaBuilderConfig
