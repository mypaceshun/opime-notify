import re
import unicodedata
from datetime import datetime, timedelta
from typing import Optional

from opime_notify.fetch_schedule import Parser, Schedule
from opime_notify.schedule import NotifySchedule


class MonthlyPhotoSchedule(Schedule):
    def __init__(
        self,
        title: str,
        date: Optional[datetime],
        type: str,
        description: str,
        url: str = "",
        start_date: datetime = None,
    ):
        self.title = title
        self.date = date
        self.type = type
        self.description = description
        self.url = url
        self.start_date = start_date

    def get_notify_schedule_list(self) -> list[NotifySchedule]:
        if self.date is None or self.start_date is None:
            return []
        date_str = self.start_date.strftime("%m月%d日%H時")
        notify_time = self.start_date - timedelta(hours=2)
        notify_message = f"""{date_str}より、{self.title}の予約販売が開始されます。
なくなり次第終了なので早めに予約しましょう！"""
        return [
            NotifySchedule(
                id=0,
                title=f"{self.title} 予約販売開始",
                date=notify_time.strftime(NotifySchedule.date_format),
                description=notify_message,
                url=self.url,
                status="BEFORE",
            )
        ]


class MonthlyPhotoParser(Parser):
    def __init__(self, schedule: MonthlyPhotoSchedule):
        self.schedule = schedule

    def parse(self) -> list[MonthlyPhotoSchedule]:
        _title = self.schedule.title
        title = _title.split("予約")[0]
        body_text = self.schedule.description
        norm_body_text = unicodedata.normalize("NFKC", body_text)
        norm_body_text = norm_body_text.replace(" ", "")
        start_date = self.parse_start_date(norm_body_text)
        if start_date is None:
            return []
        return [
            MonthlyPhotoSchedule(
                title=title,
                date=self.schedule.date,
                type=self.schedule.type,
                description=self.schedule.description,
                start_date=start_date,
            )
        ]

    def parse_start_date(self, body_text: str) -> Optional[datetime]:
        date_pattern = r"(\d+月\d+日\(.\)\d+:\d+)より、下記商品の販売を開始いたします。"
        mobj = re.search(date_pattern, body_text)
        if mobj is None:
            return None
        date_text = self._trim_week_str(mobj.group(1))
        date_format = "%m月%d日%H:%M"
        date = datetime.strptime(date_text, date_format)
        now_year = datetime.now().year
        return date.replace(year=now_year)


def schedule_to_monthly_photo_schedule(schedule: Schedule) -> MonthlyPhotoSchedule:
    return MonthlyPhotoSchedule(
        title=schedule.title,
        date=schedule.date,
        type=schedule.type,
        description=schedule.description,
    )


def filter_mpschedule_list(
    schedule_list: list[MonthlyPhotoSchedule], start_date: datetime = None
) -> list[MonthlyPhotoSchedule]:
    if start_date is None:
        return schedule_list
    slist = []
    for schedule in schedule_list:
        if schedule.start_date is None:
            continue
        if start_date < schedule.start_date:
            slist.append(schedule)
    return slist
