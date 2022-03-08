import re
from datetime import datetime, timedelta
from typing import Optional

from opime_notify.fetch_schedule import Parser, Schedule
from opime_notify.schedule import NotifySchedule


class OTSaleSchedule(Schedule):
    def __init__(
        self,
        title: str,
        date: Optional[datetime],
        type: str,
        description: str,
        zi: int = 0,
        sale_start: datetime = None,
        sale_end: datetime = None,
        cdtitle: str = "",
    ):
        self.title = title
        self.date = date
        self.type = type
        self.description = description
        self.zi = zi
        self.sale_start = sale_start
        self.sale_end = sale_end
        self.cdtitle = cdtitle

    def get_notify_schedule_list(self) -> list[NotifySchedule]:
        if self.date is None:
            return []
        notify_schedule_list = []
        date_format = NotifySchedule.date_format
        url = "https://ngt48cd.shop/"
        if self.sale_start is not None and datetime.now() < self.sale_start:
            notify_time = self.sale_start - timedelta(hours=2)
            date_str = self.sale_start.strftime("%m月%d日 %H時%M分")
            notify_message = f"""{date_str} より {self.cdtitle} オンラインおしゃべり会第{self.zi}次受付が開始されます！
今回は {self.description.strip()} となります。"""
            notify_schedule_list.append(
                NotifySchedule(
                    id=0,
                    title=f"{self.cdtitle} 第{self.zi}次受付開始",
                    date=notify_time.strftime(date_format),
                    description=notify_message,
                    url=url,
                    status="BEFORE",
                )
            )
        if self.sale_end is not None and datetime.now() < self.sale_end:
            notify_time = self.sale_end - timedelta(hours=3)
            date_str = self.sale_end.strftime("%m月%d日 %H時%M分")
            notify_message = f"""{date_str} で {self.cdtitle} オンラインおしゃべり会第{self.zi}次受付が終了します！
まだ確保していない方は無くなる前に急いで申込みしましょう！"""
            notify_schedule_list.append(
                NotifySchedule(
                    id=1,
                    title=f"{self.cdtitle} 第{self.zi}次受付終了",
                    date=notify_time.strftime(date_format),
                    description=notify_message,
                    url=url,
                    status="BEFORE",
                )
            )
        return notify_schedule_list


def schedule_to_otsale_schedule(schedule: Schedule) -> OTSaleSchedule:
    return OTSaleSchedule(
        schedule.title, schedule.date, schedule.type, schedule.description
    )


class OTSaleNewsParser(Parser):
    def __init__(self, schedule: OTSaleSchedule):
        self.schedule = schedule
        self.cdtitle = self._parse_cdtitle(self.schedule.title)
        self.schedule.title = self._text_normalize(schedule.title)
        self.schedule.description = self._text_normalize(schedule.description)

    def _parse_cdtitle(self, title):
        title_pattern = r"(NGT48.*劇場盤)"
        mobj = re.search(title_pattern, title)
        if mobj:
            return mobj.group(1)
        return title

    def parse(self) -> list[OTSaleSchedule]:
        # ご予約受付日程 -> 空行
        body_str = self.schedule.description
        over_keyword = "ご予約受付日程"
        text = body_str.split(over_keyword)[-1]
        under_keyword = "\n\n"
        text = text.split(under_keyword)[0]
        separator = "・"
        one_sale_list = text.split(separator)
        otsale_schedule_list = []
        for one_sale in one_sale_list:
            otsale_schedule = self.parse_one_sale(one_sale)
            if otsale_schedule is None:
                continue
            otsale_schedule_list.append(otsale_schedule)
        return otsale_schedule_list

    def parse_one_sale(self, one_sale_text) -> Optional[OTSaleSchedule]:
        pattern = r"第(\d+)次受付\.+(\d+/\d+\(.\)\d+:\d+)~(\d+/\d+\(.\)\d+:\d+)"
        mobj = re.search(pattern, one_sale_text)
        if mobj is None:
            return None
        now_year = datetime.now().year
        zi = int(mobj.group(1))
        sale_start_str = self._trim_week_str(mobj.group(2), " ")
        sale_end_str = self._trim_week_str(mobj.group(3), " ")
        sale_start = datetime.strptime(sale_start_str, "%m/%d %H:%M")
        sale_start = sale_start.replace(year=now_year)
        sale_end = datetime.strptime(sale_end_str, "%m/%d %H:%M")
        sale_end = sale_end.replace(year=now_year)
        description = one_sale_text.strip().split("\n")[-1]
        return OTSaleSchedule(
            title=self.schedule.title,
            date=self.schedule.date,
            type=self.schedule.type,
            description=description,
            zi=zi,
            sale_start=sale_start,
            sale_end=sale_end,
            cdtitle=self.cdtitle,
        )


def filter_otsale_schedule_list(
    otsale_schedule_list: list[OTSaleSchedule], start_date: datetime = None
) -> list[OTSaleSchedule]:
    slist = []
    for otsale_schedule in otsale_schedule_list:
        if start_date is not None and otsale_schedule.sale_end is not None:
            if otsale_schedule.sale_end < start_date:
                continue
        slist.append(otsale_schedule)
    return slist
