import re
from datetime import datetime
from typing import Optional, TypedDict, Union

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from opime_notify.fetch_schedule import Schedule
from opime_notify.fetch_schedule.theater_parser import (
    TheaterNewsParser,
    TheaterSchedule,
    schedule_to_theater_schedule,
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
        self, page: int = 1, category: int = 0, verbose: bool = False
    ) -> list[Union[Tag, NavigableString, None]]:
        url = f"{self.NEWS_URL}/articles/{page}/0/{category}"
        res = requests.get(url)
        res.raise_for_status()
        news_body_el = self._find_news_body(res.text)
        if not isinstance(news_body_el, Tag):
            return []
        news_list_el = news_body_el("a", href=re.compile(f"{self.NEWS_URL}/detail/*"))
        return news_list_el

    def fetch_schedule_detail(
        self, url: str, verbose: bool = False
    ) -> Optional[Schedule]:
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
        if verbose:
            print(f"{title=}, {date=}, {tagname=}")
        return Schedule(title=title, date=date, type=tagname, description=body_text)

    def fetch_schedule_theater(
        self,
        page: int = 1,
        verbose: bool = False,
    ) -> list[TheaterSchedule]:
        news_list_el = self.fetch_schedule_list(page=page, category=1, verbose=verbose)
        theater_schedule_list = []
        for news_el in news_list_el:
            if not isinstance(news_el, Tag):
                continue
            url = news_el.attrs.get("href", None)
            if isinstance(url, str):
                schedule = self.fetch_schedule_detail(url, verbose=verbose)
                if schedule is None:
                    continue
                _schedule = schedule_to_theater_schedule(schedule)
                parser = TheaterNewsParser(_schedule)
                theater_schedule = parser.parse(verbose=verbose)
                theater_schedule_list += theater_schedule
        return theater_schedule_list


class TagDict(TypedDict):
    id: int
    code: str
    name: str
    name_kana: str


class ShopSession:
    BASE_URL = "https://official-goods-store.jp/ngt48/"
    TAGLIST_URL = f"{BASE_URL}api/tag/lists.json?shop_id=279"

    def fetch_tag_list(self) -> list[TagDict]:
        """
        news記事のようなものが無くなってしまったのでタグ一覧で新商品を推測する
        """
        url = self.TAGLIST_URL
        res = requests.get(url)
        res.raise_for_status()
        resdict = res.json()
        taglist: list[TagDict] = resdict.get("tags", [])
        return taglist

    def generate_title(self, code: str, name: str) -> str:
        return f"[{code}]{name}"


class CDShopSession:
    BASE_URL = "https://ngt48cd.shop/"
    NEWS_URL = f"{BASE_URL}api/v1/news?group_id=5"

    def fetch_article_list(self) -> list:
        url = self.NEWS_URL
        res = requests.get(url)
        res.raise_for_status()
        resdict = res.json()
        if isinstance(resdict, list):
            return resdict
        print("fetch error")
        print(resdict)
        return []
