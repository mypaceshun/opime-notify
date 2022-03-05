import click
from rich import print


@click.command()
def cli():
    print("[bold green]run script fetch_schedule[/bold green]")
