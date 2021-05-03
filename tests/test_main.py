"""Test cases for the __main__ module."""
import os
from typing import Any
from typing import Dict

import pytest
from click.testing import CliRunner

from tf_restore_helper import __main__


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture(scope="function")
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # noqa
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # noqa
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # noqa
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # noqa


def test_main_fails_no_creds(
    runner: CliRunner, aws_credentials: Dict[Any, Any]
) -> None:
    """It exits with a status code of two."""
    result = runner.invoke(__main__.main, ["--planfile", "tests/assets/plan.json"])
    assert result.exit_code == 1
    assert (
        "Ensure you have valid aws credentials before using this tool." in result.output
    )


def test_main_error_wrong_path(runner: CliRunner) -> None:
    """It exits with a status code of two and logs a friendly message."""
    result = runner.invoke(__main__.main, ["--planfile", "../wrongpath/plan.json"])
    assert result.exit_code == 1
    assert "Please provide a valid path for a terraform plan file." in result.output
