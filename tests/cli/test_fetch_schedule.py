from click.testing import CliRunner

from opime_notify.cli.fetch_schedule import cli


def test_cli_send_line_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
