from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import (
    ButtonsTemplate,
    TemplateSendMessage,
    TextSendMessage,
    URIAction,
)

from opime_notify.schedule import NotifySchedule


class LineNotifiyer:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def notify_line_all(
        self, schedule_list: list[NotifySchedule]
    ) -> list[NotifySchedule]:
        result_list = []
        for schedule in schedule_list:
            result = self.notify_line(schedule)
            result_list.append(result)
        return result_list

    def notify_line(self, schedule: NotifySchedule) -> NotifySchedule:
        line_bot_api = LineBotApi(self.access_token)
        schedule.normalize()
        message = self.generate_message(schedule)
        result_schedule = schedule
        try:
            line_bot_api.broadcast(message)
            result_schedule.status = "SUCCESS"
        except LineBotApiError as error:
            result_schedule.status = f"{error}"
        return result_schedule

    def generate_message(self, schedule: NotifySchedule):
        if isinstance(schedule.url, str) and len(schedule.url) > 0:
            url = schedule.url
            if url.startswith("http://") or url.startswith("https://"):
                return self.generate_message_url(schedule)
        return self.generate_message_text(schedule)

    def generate_message_text(self, schedule: NotifySchedule):
        title = schedule.title
        description = schedule.description
        url = schedule.url
        message = title
        if description != "":
            message = f"{title}\n\n{description}"
        if url is not None:
            if url.startswith("http://") or url.startswith("https://"):
                message += f"\n\n{url}"
        max_len = 5000
        if len(message) > max_len:
            message = message[:max_len]
        return TextSendMessage(text=message)

    def generate_message_url(self, schedule: NotifySchedule):
        message = schedule.description
        max_len = 160
        if len(message) > max_len:
            return self.generate_message_text(schedule)
        template = ButtonsTemplate(
            text=schedule.description,
            actions=[URIAction(label="確認する", uri=schedule.url)],
        )
        message = TemplateSendMessage(alt_text=schedule.title, template=template)
        return message
