import re
import unicodedata
from datetime import datetime
from typing import Optional, Union

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from opime_notify.fetch_schedule import Schedule
from opime_notify.fetch_schedule.monthly_photo_parser import (
    MonthlyPhotoParser,
    MonthlyPhotoSchedule,
    schedule_to_monthly_photo_schedule,
)
from opime_notify.fetch_schedule.otsale_parser import (
    OTSaleNewsParser,
    OTSaleSchedule,
    schedule_to_otsale_schedule,
)
from opime_notify.fetch_schedule.theatre_parser import (
    TheatreNewsParser,
    TheatreSchedule,
    schedule_to_theatre_schedule,
)


class OfficialSession:
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

    def fetch_schedule_otsale(self, page: int = 1) -> list[OTSaleSchedule]:
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


class ShopSession:
    NEWS_URL = "https://shop.ngt48.jp/news/"

    def fetch_schedule_monthly_photo(self) -> list[MonthlyPhotoSchedule]:
        news_list_el = self.fetch_schedule_list()
        monthly_photo_schedule_list = []
        for news_el in news_list_el:
            if not isinstance(news_el, Tag):
                continue
            title = self._parse_title(news_el)
            if not self.is_monthly_photo_title(title):
                continue
            url = self._parse_url(news_el)
            if url == "":
                continue
            schedule = self.fetch_schedule_detail(url)
            if schedule is None:
                continue
            _schedule = schedule_to_monthly_photo_schedule(schedule)
            _schedule.url = url
            parser = MonthlyPhotoParser(_schedule)
            mpschedule = parser.parse()
            monthly_photo_schedule_list += mpschedule

        return monthly_photo_schedule_list

    def fetch_schedule_list(
        self, page: int = 1
    ) -> list[Union[Tag, NavigableString, None]]:
        url = self.NEWS_URL
        if page >= 2:
            url += f"page/{page}/"
        res = requests.get(url)
        res.raise_for_status()
        news_body_el = self._find_news_body(res.text)
        if news_body_el is None:
            return []
        news_list_el = news_body_el("div", "news-item")
        return news_list_el

    def fetch_schedule_detail(self, url: str) -> Optional[Schedule]:
        res = requests.get(url)
        res.raise_for_status()
        title_el = self._find_news_title(res.text)
        body_el = self._find_news_body(res.text)
        if title_el is None or body_el is None:
            return None
        title_str = self._parse_title(title_el)
        date = self._parse_datetime(title_el)
        if date is None:
            return None
        description = body_el.text.strip()
        return Schedule(title_str, date, "monthly_photo", description)

    def _find_news_title(self, htmltext: str) -> Optional[Tag]:
        soup = BeautifulSoup(htmltext, "html.parser")
        news_title_el = soup.find("div", "news-item")
        if isinstance(news_title_el, Tag):
            return news_title_el
        return None

    def _find_news_body(self, htmltext: str) -> Optional[Tag]:
        soup = BeautifulSoup(htmltext, "html.parser")
        news_body_el = soup.find("div", "entry-content")
        if isinstance(news_body_el, Tag):
            return news_body_el
        return None

    def _parse_datetime(self, news_el: Tag) -> Optional[datetime]:
        date_el = news_el.find("div", "block-1")
        if not isinstance(date_el, Tag):
            return None
        date_pattern = r"(\d{4}\.\d{2}\.\d{2})"
        date_format = "%Y.%m.%d"
        mobj = re.search(date_pattern, date_el.text)
        if mobj is None:
            return None
        date_str = mobj.group(1)
        return datetime.strptime(date_str, date_format)

    def _parse_title(self, news_el: Tag) -> str:
        title_el = news_el.find("div", "title-post")
        if not isinstance(title_el, Tag):
            return ""
        return title_el.text.strip()

    def _parse_url(self, news_el: Tag) -> str:
        title_el = news_el.find("div", "title-post")
        if not isinstance(title_el, Tag):
            return ""
        url_el = title_el.find("a")
        if not isinstance(url_el, Tag):
            return ""
        return url_el.attrs.get("href", "").strip()

    def is_monthly_photo_title(self, title: str) -> bool:
        result = False
        norm_title = unicodedata.normalize("NFKC", title)
        norm_title = norm_title.replace(" ", "")
        monthly_photo_pattern = r"\d{4}年\d+月度個別生写真\d枚セットVol.\d"
        mobj = re.search(monthly_photo_pattern, norm_title)
        if mobj is None:
            return result
        return True
