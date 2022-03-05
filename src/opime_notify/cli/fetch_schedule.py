import click
from rich import print

from opime_notify.fetch_schedule import Session


@click.command()
def cli():
    print("[bold green]run script fetch_schedule[/bold green]")
    session = Session()
    res = session.fetch_schedule_theatre()
    print(res)
