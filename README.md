# hatch-conda-build

Conda package builder for [Hatch](https://hatch.pypa.io/latest/). Hatch is modern, extensible Python project manager.

## Usage

Add `hatch-conda-build` within the build-system.requires field in your pyproject.toml file.

```toml
[build-system]
requires = ["hatchling", "hatch-conda-build"]
build-backend = "hatchling.build"
```

Additionally `conda-build` must be in your current path when running a
hatch build.

### Options

Additional builder configuration can be set in the following toml
header.

```toml
[tool.hatch.build.targets.conda]
...
```

Following table contains available customization of builder behavior.

| Option                | Type      | Default         | Description                                      |
|:----------------------|:----------|:----------------|:-------------------------------------------------|
| channels              | list[str] | ['conda-forge'] | Channels used for package build and testing      |
| default_numpy_version | str       | None            | numpy version, otherwise use conda-build default |


## Building Conda Package

The [builder plugin](https://hatch.pypa.io/latest/plugins/builder/reference/) name is called `conda`.

To start build process, run `hatch build -t conda`:

```shell
$ hatch build -t conda
[conda]
...
```

## License

Plugin hatch-conda-build is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
