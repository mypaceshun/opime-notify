import re
import unicodedata
from datetime import datetime, timedelta
from typing import Optional, Union

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from opime_notify.schedule import NotifySchedule


class TheatreSchedule:
    def __init__(
        self,
        title: str,
        date: Optional[datetime],
        type: str,
        description: str = "",
        offer_start_date: Optional[datetime] = None,
        offer_end_date: Optional[datetime] = None,
        result_date: Optional[datetime] = None,
    ):
        self.title = title
        self.date = date
        self.type = type
        self.description = description
        self.offer_start_date = offer_start_date
        self.offer_end_date = offer_end_date
        self.result_date = result_date

    def __str__(self):
        date_str = self.get_date_str()
        return f"{date_str} [{self.type}] {self.title}"

    def __repr__(self):
        self.get_date_str()
        return (
            f"TheatreSchedule({repr(self.title)}, {repr(self.date)}, {repr(self.type)})"
        )

    def get_date_str(self) -> str:
        date_format = "%Y/%m/%d %H:%M:%S"
        if self.date is None:
            return ""
        return self.date.strftime(date_format)

    def get_notify_schedule_list(self) -> list[NotifySchedule]:
        if self.date is None:
            return []
        date_format = NotifySchedule.date_format
        dmm_url = "https://www.dmm.com/lod/ngt48/"
        url = "https://ticket.akb48-group.com/home/top.php?mode=&gr=NGT48"
        notify_schedule_list = []
        notify_message = f"""本日は {self.title} です！

劇場の方は劇場で、そうでない方もDMMを見て応援しましょう！"""
        notify_time = self.date.replace(hour=9, minute=0)
        notify_schedule_list.append(
            NotifySchedule(
                id=0,
                title=self.title,
                date=notify_time.strftime(date_format),
                description=notify_message,
                url=dmm_url,
                status="BEFORE",
            )
        )
        date_str = self.date.strftime("%m月%d日 %H時%M分")
        if self.offer_start_date is not None and datetime.now() < self.offer_start_date:
            offer_start_str = self.offer_start_date.strftime("%H時%M分")
            notify_message = f"""{date_str} に開催される {self.title} の申込みが {offer_start_str} より開始します！

忘れなように申込みしましょう！"""
            notify_time = self.offer_start_date - timedelta(minutes=30)
            notify_schedule_list.append(
                NotifySchedule(
                    id=1,
                    title=f"{self.title} 申込み開始",
                    date=notify_time.strftime(date_format),
                    description=notify_message,
                    url=url,
                    status="BEFORE",
                )
            )
        if self.offer_end_date is not None and datetime.now() < self.offer_end_date:
            offer_end_str = self.offer_end_date.strftime("%H時%M分")
            notify_message = f"""{date_str} に開催される {self.title} の申込みは {offer_end_str} で終了です！

まだ申込みをしていない方は早めに申込みをしましょう！"""
            notify_time = self.offer_end_date - timedelta(hours=3)
            notify_schedule_list.append(
                NotifySchedule(
                    id=2,
                    title=f"{self.title} 申込み終了",
                    date=notify_time.strftime(date_format),
                    description=notify_message,
                    url=url,
                    status="BEFORE",
                )
            )
        if self.result_date is not None and datetime.now() < self.result_date:
            result_str = self.result_date.strftime("%H時%M分")
            notify_message = f"""{date_str} に開催される {self.title} の当落が {result_str} までに発表されます！

当たりますように🙏"""
            notify_time = self.result_date - timedelta(hours=3)
            notify_schedule_list.append(
                NotifySchedule(
                    id=3,
                    title=f"{self.title} 抽選結果発表",
                    date=notify_time.strftime(date_format),
                    description=notify_message,
                    url=url,
                    status="BEFORE",
                )
            )
        return notify_schedule_list


class Session:
    NEWS_URL = "https://ngt48.jp/news"

    def _find_news_body(self, htmltext: str) -> Union[Tag, NavigableString, None]:
        soup = BeautifulSoup(htmltext, "html.parser")
        news_body_el = soup.find("div", "news-block-inner")
        return news_body_el

    def _split_tag_and_title(self, title_el: Tag) -> tuple[str, str]:
        tag_el = title_el.span
        tagname = ""
        title = ""
        if isinstance(tag_el, Tag):
            tagname = tag_el.text.strip()
            title_text = tag_el.next_sibling
            if isinstance(title_text, NavigableString):
                title = title_text.strip()
        else:
            title = title_el.text.strip()
        return (tagname, title)

    def _parse_datetime(self, date_el: Tag) -> Optional[datetime]:
        _datestr = date_el.text.strip()
        pattern = r"\d{4}\.\d{2}\.\d{2}"
        mobj = re.match(pattern, _datestr)
        if mobj is None:
            return None
        datestr = mobj.group(0)
        datetime_pattern = "%Y.%m.%d"
        return datetime.strptime(datestr, datetime_pattern)

    def fetch_schedule_list(
        self, page: int = 1, category: int = 0
    ) -> list[Union[Tag, NavigableString, None]]:
        url = f"{self.NEWS_URL}/articles/{page}/0/{category}"
        res = requests.get(url)
        res.raise_for_status()
        news_body_el = self._find_news_body(res.text)
        if not isinstance(news_body_el, Tag):
            return []
        news_list_el = news_body_el("a", href=re.compile(f"{self.NEWS_URL}/detail/*"))
        return news_list_el

    def fetch_schedule_detail(self, url: str) -> Optional[TheatreSchedule]:
        res = requests.get(url)
        res.raise_for_status()
        news_body_el = self._find_news_body(res.text)
        if not isinstance(news_body_el, Tag):
            return None
        title_el = news_body_el.find("div", "title")
        if not isinstance(title_el, Tag):
            return None
        tagname, title = self._split_tag_and_title(title_el)
        date_el = news_body_el.find("div", "date")
        if not isinstance(date_el, Tag):
            return None
        date = self._parse_datetime(date_el)
        body_el = news_body_el.find("div", "content")
        body_text = ""
        if isinstance(body_el, Tag):
            body_text = body_el.text.strip()
        return TheatreSchedule(
            title=title, date=date, type=tagname, description=body_text
        )

    def fetch_schedule_theatre(
        self,
        page: int = 1,
    ):
        news_list_el = self.fetch_schedule_list(page=page, category=1)
        theatre_schedule_list = []
        for news_el in news_list_el:
            if not isinstance(news_el, Tag):
                continue
            url = news_el.attrs.get("href", None)
            if isinstance(url, str):
                schedule = self.fetch_schedule_detail(url)
                if schedule is None:
                    continue
                parser = TheatreNewsParser(schedule)
                theatre_schedule = parser.parse()
                theatre_schedule_list += theatre_schedule
        return theatre_schedule_list


class TheatreNewsParser:
    def __init__(self, schedule: TheatreSchedule):
        self.schedule = schedule
        self.schedule.title = self._text_normalize(schedule.title)
        self.schedule.description = self._text_normalize(schedule.description)
        self.news_type = self._get_news_type()
        self.offer_start: Optional[datetime] = None
        self.offer_end: Optional[datetime] = None
        self.result_date: Optional[datetime] = None

    def _text_normalize(self, text: str) -> str:
        _text = unicodedata.normalize("NFKC", text)
        _text = _text.replace(" ", "")
        return _text

    def _get_news_type(self) -> str:
        type = "special"
        pattern = r"^\d{4}年\d+月\d+日\(.\)~\d+月\d+日\(.\)NGT48劇場公演スケジュールのご案内"
        mobj = re.match(pattern, self.schedule.title)
        if mobj:
            type = "normal"
        return type

    def parse(self) -> list[TheatreSchedule]:
        if self.news_type == "normal":
            return self.parse_normal()
        return []

    def parse_normal(self) -> list[TheatreSchedule]:
        body_str = self.schedule.description
        self.parse_offer_date(body_str)
        under_keyword = "【チケット申込について】"
        body_str = body_str.split(under_keyword)[0]
        date_separator = "●"
        body_date_list = body_str.split(date_separator)
        schedule_list = []
        for body_onedate in body_date_list:
            schedule_list += self.parse_body_onedate(body_onedate)
        return schedule_list

    def parse_offer_date(self, text: str) -> None:
        # 申込み期間 -> 空行まで
        over_keyword = "申込期間"
        text = text.split(over_keyword)[-1]
        under_keyword = "\n\n"
        text = text.split(under_keyword)[0]
        offer_pattern = r"(\d{4}年\d+月\d+日\(.\)\d{2}:\d{2})~(\d+月\d+日\(.\)\d{2}:\d{2})まで"
        result_pattern = r"当落発表:(\d+月\d+日\(.\)\d{2}:\d{2})まで"
        now_year = datetime.now().year
        moffer = re.search(offer_pattern, text)
        if moffer:
            offer_start_str = self._trim_week_str(moffer.group(1))
            offer_end_str = self._trim_week_str(moffer.group(2))
            self.offer_start = datetime.strptime(offer_start_str, "%Y年%m月%d日%H:%M")
            self.offer_end = datetime.strptime(offer_end_str, "%m月%d日%H:%M")
            self.offer_end = self.offer_end.replace(year=now_year)

        mresult = re.search(result_pattern, text)
        if mresult:
            result_date_str = self._trim_week_str(mresult.group(1))
            self.result_date = datetime.strptime(result_date_str, "%m月%d日%H:%M")
            self.result_date = self.result_date.replace(year=now_year)

    def _trim_week_str(self, text: str) -> str:
        return re.sub(r"\(.\)", "", text)

    def parse_body_onedate(self, onedate_text: str) -> list[TheatreSchedule]:
        closed_keyword = "休館日"
        if closed_keyword in onedate_text:
            return []
        # 先頭行は日付であるとする
        date_pattern = r"\d+月\d+日"
        date_format = "%m月%d日"
        m = re.search(date_pattern, onedate_text)
        if m is None:
            return []
        date_str = m.group(0)
        onedate = datetime.strptime(date_str, date_format)
        _date = self.schedule.date
        year = datetime.now().year
        if isinstance(_date, datetime):
            year = _date.year
        onedate = onedate.replace(year=year)
        sections = onedate_text.split("\n\n")
        schedule_list = []
        for section in sections:
            schedule = self.parse_section_onedate(section, onedate)
            if schedule is None:
                continue
            schedule_list.append(schedule)
        return schedule_list

    def parse_section_onedate(
        self, section_text: str, onedate: datetime
    ) -> Optional[TheatreSchedule]:
        section_lines = section_text.split("\n")
        title = ""
        date = onedate
        type = "theater"
        description = ""
        suffix = ""
        DAY = "昼公演"
        NIGHT = "夜公演"
        for line in section_lines:
            if DAY in line or NIGHT in line:
                if DAY in line:
                    suffix = DAY
                elif NIGHT in line:
                    suffix = NIGHT
                pattern = r"\d+:\d+"
                date_format = "%H:%M"
                m = re.search(pattern, line)
                if m is None:
                    continue
                date_str = m.group(0)
                open_date = datetime.strptime(date_str, date_format)
                date = date.replace(hour=open_date.hour, minute=open_date.minute)
            elif "演目" in line:
                separator = ":"
                title = line.split(separator)[-1]
            elif "出演メンバー" in line or description != "":
                description += line
        if title == "" or date == onedate:
            return None
        if suffix != "":
            title = f"{title}【{suffix}】"
        return TheatreSchedule(
            title=title,
            date=date,
            type=type,
            description=description,
            offer_start_date=self.offer_start,
            offer_end_date=self.offer_end,
            result_date=self.result_date,
        )


def filter_theatre_schedule_list(
    theatre_schedule_list: list[TheatreSchedule],
    keywords: Optional[list[str]] = None,
    start_date: Optional[datetime] = None,
) -> list[TheatreSchedule]:
    if keywords is None:
        keywords = []
    _theatre_schedule_list = []
    for theatre_schedule in theatre_schedule_list:
        if start_date is not None and theatre_schedule.date is not None:
            if theatre_schedule.date < start_date:
                continue
        for keyword in keywords:
            if (
                keyword in theatre_schedule.description
                or keyword in theatre_schedule.title
            ):
                _theatre_schedule_list.append(theatre_schedule)
    return _theatre_schedule_list
