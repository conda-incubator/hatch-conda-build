from pathlib import Path
from hatch_conda_build.plugin import CondaBuilder


def test_requires_python(project_factory):
    project = project_factory(requires_python=">=3.10")
    builder = CondaBuilder(root=project)
    requirements = builder._get_requirements()

    assert "python >=3.10" in requirements["run"]
    assert "python >=3.10" in requirements["host"]


def test_pypi_conversion(project_factory):
    project = project_factory(
        name="project-a", package_name="project_a", version="0.1.0",
        requires_python=">=3.9",
        dependencies=["requests==2.31.0", "Flask", "build", "art", "pydantic[email]<2"])

    builder = CondaBuilder(root=project)
    requirements = builder._get_requirements()

    assert requirements["run"] == [
        'python >=3.9',
        'requests ==2.31.0',
        'flask',
        'python-build',
        'ascii-art',
        'pydantic <2'
    ]

    assert requirements["host"] == ["python >=3.9", "hatchling", "pip"]


def test_recipe(project_factory):
    project = project_factory()

    builder = CondaBuilder(root=project)
    recipe = builder._construct_recipe()

    assert recipe["package"]["name"] == "project-a"
    assert recipe["package"]["version"] == "0.1.0"
    assert recipe["source"]["path"] == str(project)
    assert recipe["build"]["noarch"] == "python"
    assert recipe["build"]["number"] == 0
    assert "--no-build-isolation" in recipe["build"]["script"]
    assert recipe["requirements"]["host"] == ["python >=3.8", "hatchling", "pip"]
    assert recipe["requirements"]["run"] == ["python >=3.8", "requests"]
    assert recipe["about"]["home"] == "https://example.org"
    assert recipe["about"]["summary"] == "A description"


def test_noarch_build(project_factory):
    project = project_factory()

    builder = CondaBuilder(root=project)
    _package = builder.build_standard(project / "dist")
    package = Path(_package)

    assert package.exists()
    assert (package.parent / "repodata.json").exists()
    assert package.parent.name == "noarch"
    assert package.parent.parent.name == "conda"
