from datetime import datetime
from pathlib import Path

import click
from rich import print

from opime_notify.fetch_schedule import Session, filter_theatre_schedule_list
from opime_notify.gsheet import GsheetSession


@click.command()
@click.option("--gsheet-id", help="cache spread sheet id", envvar="GSHEET_ID")
@click.option(
    "--google-json-key",
    help="google json key file",
    type=click.Path(),
    envvar="GOOGLE_JSON_KEY_FILE",
)
def cli(gsheet_id, google_json_key):
    print("[bold green]run script fetch_schedule[/bold green]")
    session = Session()
    theatre_schedule_list = session.fetch_schedule_theatre()
    theatre_schedule_list = filter_theatre_schedule_list(
        theatre_schedule_list, keywords=["中井りか"], start_date=datetime.now()
    )
    print("theatre_schedule_list")
    print(theatre_schedule_list)
    notify_schedule_list = []
    for theatre_schedule in theatre_schedule_list:
        notify_schedule_list += theatre_schedule.get_notify_schedule_list()
    print("notify_schedule_list")
    print(notify_schedule_list)

    json_key_file = Path(google_json_key).expanduser()
    gsession = GsheetSession(json_key_file, gsheet_id)
    all_schedule = gsession.read_all_schedule()
    gsession.clear_schedule()
    gsession.write_all_schedule(all_schedule + notify_schedule_list)
