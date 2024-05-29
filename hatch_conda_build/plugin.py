import json
# import tomli
import shutil
import typing
import pathlib
import collections
import tempfile
import subprocess

from hatchling.builders.plugin.interface import BuilderInterface

from hatch_conda_build.config import CondaBuilderConfig


def normalize_pypi_packages(packages: typing.List[str]):
    _packages = []
    for package in packages:
        if "hatch-conda-build" in package:
            continue

        if "@" in package:
            package = package.split("@")[0]

        _packages.append(package)
    return _packages


def construct_meta_yaml_from_pyproject(metadata, target_config):
    py_meta = metadata.core_raw_metadata
    conda_meta = collections.defaultdict(dict)

    from grayskull.strategy.py_base import merge_setup_toml_metadata
    from grayskull.strategy.py_toml import get_all_toml_info
    from souschef.recipe import Recipe
    from grayskull.config import Configuration
    from grayskull.strategy.pypi import extract_requirements, extract_optional_requirements, normalize_requirements_list
    from grayskull.strategy.pypi import merge_pypi_sdist_metadata

    # python -c 'import build.util; build.util.project_wheel_metadata('.', isolated=True)['Version"]'
    pyproject_toml = pathlib.Path(metadata._project_file)

    # import build.util
    # wheel_metadata = build.util.project_wheel_metadata(pyproject_toml.parent, isolated=False)

    conda_meta["package"]["name"] = metadata.name
    conda_meta["package"]["version"] = metadata.version

    recipe = Recipe(name=metadata.name, version=metadata.version)
    config = Configuration(name=metadata.name, version=metadata.version, from_local_sdist=True)

    # source
    full_metadata = get_all_toml_info(pyproject_toml)
    merged = merge_setup_toml_metadata({}, full_metadata)
    merged2 = merge_pypi_sdist_metadata({}, merged, config)

    reqs = extract_requirements(merged2, config, recipe)

    for key in reqs:
        reqs[key] = normalize_requirements_list(reqs[key], config)

    # package

    conda_meta["source"]["path"] = str(pyproject_toml.parent)
    # with pyproject_toml.open("rb") as f:
    #     full_metadata = tomli.load(f)

    # build
    conda_meta["build"]["number"] = 0
    conda_meta["build"]["noarch"] = "python"
    conda_meta["build"][
        "script"
    ] = "{{ PYTHON }} -m pip install --no-deps --ignore-installed . -vv"

    # requirements
    # if "requires-python" in py_meta:
    #     python_spec = f"python {py_meta['requires-python']}"
    # else:
    #     python_spec = "python"

    conda_meta["requirements"]["build"] = []

    # conda_meta["requirements"]["host"] = [
    #     python_spec,
    #     "pip",
    # ] + normalize_pypi_packages(full_metadata["build-system"]["requires"])

    # this is a local method to drop
    conda_meta["requirements"]["host"] = normalize_pypi_packages(reqs["host"])

    # conda_meta["requirements"]["run"] = [
    #     python_spec,
    # ] + py_meta["dependencies"]
    conda_run_deps = target_config.get("run", [])
    conda_meta["requirements"]["run"] = reqs["run"] + conda_run_deps

    conda_meta["requirements"]["run_constrained"] = target_config.get("run_constrained", [])

    # test
    conda_meta["test"] = {}

    # about
    if "homepage" in full_metadata["project"].get("urls", {}):
        conda_meta["about"]["home"] = full_metadata["project"]["urls"]["homepage"]

    if "description" in full_metadata["project"]:
        conda_meta["about"]["summary"] = full_metadata["project"]["description"]

    return conda_meta


def conda_build(
    meta_config: typing.Dict,
    build_directory: pathlib.Path,
    output_directory: pathlib.Path,
    channels: typing.List[str],
    default_numpy_version: str,
):
    print("meta.yaml: ", meta_config)
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
        "--numpy",
        default_numpy_version,
    ]
    for channel in channels:
        command += ["--channel", channel]
    print("command", command)

    import sys

    subprocess.run(command, check=True, stderr=sys.stderr, stdout=sys.stdout)

    package_name = (
        f"{meta_config['package']['name']}-"
        f"{meta_config['package']['version']}-"
        f"py_{meta_config['build']['number']}.tar.bz2"
    )
    return output_directory / "noarch" / package_name


class CondaBuilder(BuilderInterface):
    PLUGIN_NAME = "conda"

    def get_version_api(self) -> typing.Dict:
        return {"standard": self.build_standard}

    def clean(self, directory: str, versions: typing.List[str]):
        shutil.rmtree(directory)

    def build_standard(self, directory: str, **build_data: typing.Dict) -> str:
        directory = pathlib.Path(directory) / "conda"

        target_config = self.build_config.get("targets", {}).get("conda", {})
        conda_meta = construct_meta_yaml_from_pyproject(self.metadata, target_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = pathlib.Path(tmpdir)

            conda_build_filename = conda_build(
                conda_meta,
                build_directory=tmpdir,
                output_directory=directory,
                channels=target_config.get("channels", ["defaults"]),
                default_numpy_version=target_config.get(
                    "default_numpy_version", "1.22"
                ),
            )
            # shutil.copy2(conda_build_filename, directory / conda_build_filename.name)
            # subprocess.run(["conda", "index", directory])

        return str(directory)

    @classmethod
    def get_config_class(cls):
        return CondaBuilderConfig
