import json
import tomllib
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


def construct_meta_yaml_from_pyproject(metadata):
    py_meta = metadata.core_raw_metadata
    conda_meta = collections.defaultdict(dict)

    # package
    conda_meta["package"]["name"] = metadata.name
    conda_meta["package"]["version"] = metadata.version

    # source
    pyproject_toml = pathlib.Path(metadata._project_file)
    conda_meta["source"]["path"] = str(pyproject_toml.parent)
    with pyproject_toml.open("rb") as f:
        full_metadata = tomllib.load(f)

    # build
    conda_meta["build"]["number"] = 0
    conda_meta["build"]["noarch"] = "python"
    conda_meta["build"][
        "script"
    ] = "python -m pip install --no-deps --ignore-installed ."

    # requirements
    if "requires-python" in py_meta:
        python_spec = f"python {py_meta['requires-python']}"
    else:
        python_spec = "python"

    conda_meta["requirements"]["build"] = []

    conda_meta["requirements"]["host"] = [
        python_spec,
        "pip",
    ] + normalize_pypi_packages(full_metadata["build-system"]["requires"])

    conda_meta["requirements"]["run"] = [
        python_spec,
    ] + py_meta["dependencies"]

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
        "conda-build",
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

    def clean(directory: str, versions: typing.List[str]):
        shutil.rmtree(directory)

    def build_standard(self, directory: str, **build_data: typing.Dict) -> str:
        directory = pathlib.Path(directory)

        conda_meta = construct_meta_yaml_from_pyproject(self.metadata)
        target_config = self.build_config.get("targets", {}).get("conda", {})

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = pathlib.Path(tmpdir)

            conda_build_filename = conda_build(
                conda_meta,
                build_directory=tmpdir,
                output_directory=tmpdir,
                channels=target_config.get("channels", ["conda-forge"]),
                default_numpy_version=target_config.get(
                    "default_numpy_version", "1.22"
                ),
            )
            shutil.copy2(conda_build_filename, directory / conda_build_filename.name)

        return str(directory)

    @classmethod
    def get_config_class(cls):
        return CondaBuilderConfig
