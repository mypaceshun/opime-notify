import re
import unicodedata
from datetime import datetime
from typing import Optional, Union

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from opime_notify.fetch_schedule import Schedule
from opime_notify.fetch_schedule.otsale_parser import (
    OTSaleNewsParser,
    schedule_to_otsale_schedule,
)
from opime_notify.fetch_schedule.theatre_parser import (
    TheatreNewsParser,
    TheatreSchedule,
    schedule_to_theatre_schedule,
)


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

    def fetch_schedule_theatre(
        self,
        page: int = 1,
    ) -> list[TheatreSchedule]:
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
                _schedule = schedule_to_theatre_schedule(schedule)
                parser = TheatreNewsParser(_schedule)
                theatre_schedule = parser.parse()
                theatre_schedule_list += theatre_schedule
        return theatre_schedule_list

    def fetch_schedule_otsale(self, page: int = 1):
        """
        otsale -> online talk sale
        """
        info_el_list = self.fetch_schedule_list(page=page, category=11)
        otsale_info_pattern = r"シングル劇場盤<第\d+次〜第\d+次申込>受付開始のお知らせ"
        otsale_schedule_list = []
        for info_el in info_el_list:
            if not isinstance(info_el, Tag):
                continue
            title_el = info_el.find("div", "title")
            if not isinstance(title_el, Tag):
                continue
            _, title = self._split_tag_and_title(title_el)
            _title = unicodedata.normalize("NFKC", title)
            _title = _title.replace(" ", "")
            mobj = re.search(otsale_info_pattern, _title)
            if mobj is None:
                continue
            url = info_el.attrs.get("href", None)
            if isinstance(url, str):
                schedule = self.fetch_schedule_detail(url)
                if schedule is None:
                    continue
                _schedule = schedule_to_otsale_schedule(schedule)
                parser = OTSaleNewsParser(_schedule)
                otsale_schedule = parser.parse()
                otsale_schedule_list += otsale_schedule

        return otsale_schedule_list
