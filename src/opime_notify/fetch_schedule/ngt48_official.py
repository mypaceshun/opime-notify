import re
from datetime import datetime
from typing import Optional, Union

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


class Schedule:
    def __init__(
        self,
        title: str,
        date: Optional[datetime],
        type: str,
        description: str = "",
    ):
        self.title = title
        self.date = date
        self.type = type
        self.description = description

    def __str__(self):
        date_str = self.get_date_str()
        return f"{date_str} [{self.type}] {self.title}"

    def __repr__(self):
        self.get_date_str()
        return f"Schedule({repr(self.title)}, {repr(self.date)}, {repr(self.type)})"

    def get_date_str(self):
        date_format = "%Y/%m/%d %H:%M:%S"
        return self.date.strftime(date_format)


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

    def fetch_schedule_detail(self, url: str) -> Optional[Schedule]:
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
        return Schedule(title=title, date=date, type=tagname, description=body_text)

    def fetch_schedule_theatre(self, page: int = 1):
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
    def __init__(self, schedule: Schedule):
        self.schedule = schedule
        self.news_type = self._get_news_type()

    def _get_news_type(self) -> str:
        type = "special"
        pattern = r"^\d{4}年\d+月\d+日（.）～.*NGT48劇場 公演スケジュールのご案内"
        mobj = re.match(pattern, self.schedule.title)
        if mobj:
            type = "normal"
        return type

    def parse(self) -> list[Schedule]:
        if self.news_type == "normal":
            return self.parse_normal()
        return []

    def parse_normal(self) -> list[Schedule]:
        body_str = self.schedule.description
        under_keyword = "【チケット申込について】"
        body_str = body_str.split(under_keyword)[0]
        date_separator = "●"
        body_date_list = body_str.split(date_separator)
        schedule_list = []
        for body_onedate in body_date_list:
            schedule_list += self.parse_body_onedate(body_onedate)
        return schedule_list

    def parse_body_onedate(self, onedate_text: str) -> list[Schedule]:
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
    ) -> Optional[Schedule]:
        section_lines = section_text.split("\n")
        title = ""
        date = onedate
        type = "theater"
        description = ""
        for line in section_lines:
            if "昼公演" in line or "夜公演" in line:
                pattern = r"\d+[：:]\d+"
                date_format = "%H:%M"
                m = re.search(pattern, line)
                if m is None:
                    continue
                date_str = m.group(0)
                date_str = date_str.replace("：", ":")
                open_date = datetime.strptime(date_str, date_format)
                date = date.replace(hour=open_date.hour, minute=open_date.minute)
            elif "演目" in line:
                separator = "："
                title = line.split(separator)[-1]
            elif "出演メンバー" in line or description != "":
                description += line
        if title == "" or date == onedate:
            return None
        return Schedule(title=title, date=date, type=type, description=description)
