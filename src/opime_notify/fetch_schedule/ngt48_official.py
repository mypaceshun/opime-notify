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
        schedule_list = []
        for news_el in news_list_el:
            if not isinstance(news_el, Tag):
                continue
            url = news_el.attrs.get("href", None)
            if isinstance(url, str):
                schedule = self.fetch_schedule_detail(url)
                schedule_list.append(schedule)
        return schedule_list
