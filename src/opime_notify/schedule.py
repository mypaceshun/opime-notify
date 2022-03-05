from datetime import datetime
from typing import Optional


class NotifySchedule:
    def __init__(
        self,
        id: int,
        title: str,
        date: str,
        description: str = None,
        url: str = None,
        status: str = None,
        **kwargs,
    ):
        self.date_format = "%Y/%m/%d %H:%M:%S"
        self.id = id
        self.title = title
        self.date = date
        self.description = description
        self.url = url
        self.status = status

    def __str__(self):
        return ",".join(
            [self.id, self.title, self.date, self.description, self.url, self.status]
        )

    def __repr__(self):
        arglist = [
            self.id,
            self.title,
            self.date,
            self.description,
            self.url,
            self.status,
        ]
        args = ", ".join([repr(s) for s in arglist])
        return f"NotifySchedule({args})"

    def get_date(self) -> datetime:
        return datetime.strptime(self.date, self.date_format)

    def get_value(self, key: str) -> Optional[str]:
        if key == "id":
            return str(self.id)
        elif key == "title":
            return self.title
        elif key == "date":
            return self.date
        elif key == "description":
            return self.description
        elif key == "url":
            return self.url
        elif key == "status":
            return self.status
        else:
            return ""


def filter_notify_schedule(
    schedule_list: list[NotifySchedule], basetime: datetime = None
) -> list[NotifySchedule]:
    if basetime is None:
        basetime = datetime.now()
    notify_schedule_list = []
    for schedule in schedule_list:
        date = schedule.get_date()
        if date < basetime:
            notify_schedule_list.append(schedule)
    return notify_schedule_list


def marge_result_schedule(
    schedule_list: list[NotifySchedule], result_list: list[NotifySchedule]
) -> list[NotifySchedule]:
    slist = []
    for schedule in schedule_list:
        id = schedule.id
        result_schedule = get_schedule_by_id(result_list, id)
        if result_schedule is None:
            slist.append(schedule)
            continue
        if result_schedule.status == "SUCCESS":
            continue
        slist.append(result_schedule)  # ERROR
    return slist


def get_schedule_by_id(
    schedule_list: list[NotifySchedule], id: Optional[int]
) -> Optional[NotifySchedule]:
    if id is None:
        return None
    for schedule in schedule_list:
        if schedule.id == id:
            return schedule
    return None
