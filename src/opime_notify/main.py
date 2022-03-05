from pathlib import Path

import click
from dotenv import load_dotenv
from rich import print

from opime_notify.gsheet import GsheetSession
from opime_notify.notify import LineNotifiyer
from opime_notify.schedule import filter_notify_schedule, marge_result_schedule

load_dotenv()


@click.command()
@click.option(
    "--line-access-token", help="line access token", envvar="LINE_ACCESS_TOKEN"
)
@click.option("--gsheet-id", help="cache spread sheet id", envvar="GSHEET_ID")
@click.option(
    "--google-json-key",
    help="google json key file",
    type=click.Path(),
    envvar="GOOGLE_JSON_KEY_FILE",
)
def cli(line_access_token, gsheet_id, google_json_key):
    json_key_file = Path(google_json_key).expanduser()
    gsession = GsheetSession(json_key_file, gsheet_id)
    all_schedule = gsession.read_all_schedule()
    notify_schedule_list = filter_notify_schedule(all_schedule)
    print("notify_schedule_list")
    print(f"{notify_schedule_list}")
    line_notifiyer = LineNotifiyer(line_access_token)
    result_list = line_notifiyer.notify_line_all(notify_schedule_list)
    new_schedule_list = marge_result_schedule(all_schedule, result_list)
    gsession.clear_schedule()
    gsession.write_all_schedule(new_schedule_list)
