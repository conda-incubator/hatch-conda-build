from hatch_conda_build.plugin import CondaBuilder, construct_meta_yaml_from_pyproject


def test_requires_python(project_metadata_factory):
    metadata = project_metadata_factory(requires_python=">=3.10")
    builder = CondaBuilder(metadata.root, metadata=metadata)

    recipe = construct_meta_yaml_from_pyproject(metadata, builder.config.target_config)
    assert "python >=3.10" in recipe["requirements"]["run"]


def test_pypi_conversion(project_metadata_factory):
    metadata = project_metadata_factory(
        name="project-a", package_name="project_a", version="0.1.0",
        dependencies=["requests", "Flask", "build", "art", "pydantic[email]<2"])

    builder = CondaBuilder(metadata.root, metadata=metadata)
    recipe = construct_meta_yaml_from_pyproject(metadata, builder.config.target_config)

    assert recipe["requirements"]["run"] == [
        'python >=3.8',
        'requests',
        'flask',
        'python-build',
        'ascii-art',
        'pydantic <2'
    ]
