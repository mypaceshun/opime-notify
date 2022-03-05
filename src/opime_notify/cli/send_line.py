import click
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import (
    ConfirmTemplate,
    MessageAction,
    TemplateSendMessage,
    TextSendMessage,
    URIAction,
)
from rich import print
from rich.prompt import Prompt


@click.command()
@click.option(
    "--access-token",
    help="channel access token for LINE Messaging API",
    envvar="CHANNEL_ACCESS_TOKEN",
)
@click.option(
    "--type",
    help="send message type",
    type=click.Choice(["text", "confirm"]),
    default="text",
    show_default=True,
)
@click.argument("text", type=str)
def cli(access_token: str, type: str, text: str) -> None:
    print("[bold green]run script send_line![/bold green]")
    if access_token is None:
        access_token = Prompt.ask("Enter channel access token")

    line_bot_api = LineBotApi(access_token)
    message = None
    if type == "text":
        message = TextSendMessage(text=text)
    elif type == "confirm":
        message = TemplateSendMessage(
            alt_text="Confirm template",
            template=ConfirmTemplate(
                text=text,
                actions=[
                    MessageAction(label="message", text="test text"),
                    URIAction(
                        label="uri", uri="https://www.instagram.com/rika___n24x/"
                    ),
                ],
            ),
        )
    try:
        res = line_bot_api.broadcast(message)
        print(res.request_id)
    except LineBotApiError as error:
        print(error)
