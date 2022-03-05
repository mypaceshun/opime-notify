from datetime import datetime

import pytest
from click.testing import CliRunner

from opime_notify.cli.send_line import cli


def test_cli_send_line_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


@pytest.mark.LINE
def test_cli_send_line_real():
    nowstr = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    message = f"Test message from pytest [{nowstr}]"
    runner = CliRunner()
    result = runner.invoke(cli, [message])
    assert result.exit_code == 0
