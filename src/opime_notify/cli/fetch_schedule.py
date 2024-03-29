from datetime import datetime
from pathlib import Path

import click
from rich import print

from opime_notify.fetch_schedule.session import OfficialSession
from opime_notify.fetch_schedule.theater_parser import filter_theater_schedule_list
from opime_notify.gsheet import GsheetSession
from opime_notify.schedule import NotifySchedule


@click.command()
@click.option("--gsheet-id", help="cache spread sheet id", envvar="GSHEET_ID")
@click.option(
    "--google-json-key",
    help="google json key file",
    type=click.Path(),
    envvar="GOOGLE_JSON_KEY_FILE",
)
@click.option(
    "--no-regist",
    "-n",
    help="no regist google spread sheet",
    is_flag=True,
    default=False,
)
@click.option("--verbose", "-v", help="verbose output", is_flag=True, default=False)
def cli(gsheet_id, google_json_key, no_regist, verbose):
    print("[bold green]run script fetch_schedule[/bold green]")
    osession = OfficialSession()
    notify_schedule_list = []
    notify_schedule_list += _fetch_theater_schedule_list(osession, verbose=verbose)

    if len(notify_schedule_list) == 0:
        print("notify_schedule_list is empty")
        return
    print("notify_schedule_list")
    print(notify_schedule_list)

    json_key_file = Path(google_json_key).expanduser()
    gsession = GsheetSession(json_key_file, gsheet_id)
    all_schedule = gsession.read_all_schedule()
    all_schedule += notify_schedule_list
    print("all_schedule")
    print(all_schedule)
    if not no_regist:
        gsession.clear_schedule()
        gsession.write_all_schedule(all_schedule)


def _fetch_theater_schedule_list(
    session: OfficialSession, verbose: bool = False
) -> list[NotifySchedule]:
    theater_schedule_list = session.fetch_schedule_theater(verbose=verbose)
    if verbose:
        print("all theater_schedule_list")
        print(theater_schedule_list)
    theater_schedule_list = filter_theater_schedule_list(
        theater_schedule_list, keywords=["中井りか"], start_date=datetime.now()
    )
    print("theater_schedule_list")
    print(theater_schedule_list)
    notify_schedule_list = []
    for theater_schedule in theater_schedule_list:
        notify_schedule_list += theater_schedule.get_notify_schedule_list()
    return notify_schedule_list
