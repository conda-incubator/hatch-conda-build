import sys
import subprocess

import pytest
from pytest import MonkeyPatch


def hatch_build_target(target: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "hatch", "build", "-t", target],
        capture_output=False,
        check=True,
    )


@pytest.mark.slow()
def test_build(project_factory, monkeypatch: MonkeyPatch) -> None:
    project = project_factory(
        name="project-a",
        package_name="project_a",
        version="0.1.0",
        dependencies=["requests"],
    )

    monkeypatch.chdir(project)

    hatch_build_target("conda")
