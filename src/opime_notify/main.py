from pathlib import Path

import click
from dotenv import load_dotenv
from rich import print

from opime_notify.gsheet import GsheetSession
from opime_notify.notify import LineNotifiyer
from opime_notify.realtime.mpadapter import MPAdapter
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
    print("all_schedule")
    print(f"{all_schedule}")
    notify_schedule_list = filter_notify_schedule(all_schedule)
    if len(notify_schedule_list) == 0:
        print("notify_schedule_list is empty")
        return
    print("notify_schedule_list")
    print(f"{notify_schedule_list}")
    line_notifiyer = LineNotifiyer(line_access_token)
    result_list = line_notifiyer.notify_line_all(notify_schedule_list)
    new_schedule_list = marge_result_schedule(all_schedule, result_list)
    print("new_schedule_list")
    print(f"{new_schedule_list}")
    gsession.clear_schedule()
    gsession.write_all_schedule(new_schedule_list)


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
def realtime(line_access_token, gsheet_id, google_json_key):
    json_key_file = Path(google_json_key).expanduser()
    gsession = GsheetSession(json_key_file, gsheet_id)

    all_adapter = []
    all_adapter.append(MPAdapter())

    notify_article_list = []
    for adapter in all_adapter:
        curr_article_list = adapter.fetch_curr_article(gsession)
        print("curr_article_list")
        print(f"{curr_article_list}")
        _notify_article_list = adapter.fetch_notify_article_list(curr_article_list)
        if len(_notify_article_list) == 0:
            continue
        print("notify_article_list")
        print(f"{_notify_article_list}")
        adapter.regist_article(_notify_article_list + curr_article_list, gsession)
        notify_article_list += _notify_article_list
    if len(notify_article_list):
        print("notify_article is empty")
        return
    print("notify_article_list")
    print(notify_article_list)
    notify_list = []
    for notify_article in notify_article_list:
        notify_list += notify_article.get_notify_list()
    line_notifiyer = LineNotifiyer(line_access_token)
    result_list = line_notifiyer.notify_line_all(notify_list)
    print("result_list")
    print(f"{result_list}")
