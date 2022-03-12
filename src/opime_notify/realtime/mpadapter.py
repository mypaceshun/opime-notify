import unicodedata
from datetime import datetime
from typing import Optional

from bs4.element import Tag

from opime_notify.fetch_schedule.session import ShopSession
from opime_notify.gsheet import GsheetSession
from opime_notify.realtime import BaseAdapter, BaseArticle
from opime_notify.schedule import NotifySchedule


class MPArticle(BaseArticle):
    def __init__(
        self, title: str = "", date: Optional[datetime] = None, title_hash: str = ""
    ):
        self.type = "MPArticle"
        self.title = title
        self.date = date
        if title_hash is None:
            self.calc_title_hash()
        else:
            self.title_hash = title_hash

    def __str__(self):
        return f"{self.type=} {self.title=}, {self.date=}"

    def __repr__(self):
        return f"{self.type}({repr(self.title)}, {repr(self.date)})"

    def calc_title_hash(self):
        norm_title = unicodedata.normalize("NFKC", self.title)
        norm_title = norm_title.replace(" ", "")
        self.title_hash = hash(norm_title)

    def get(self, key) -> str:
        if key == "title":
            return self.title
        elif key == "date":
            if self.date is None:
                return ""
            return self.date.strftime(NotifySchedule.date_format)
        elif key == "title_hash":
            return self.title_hash
        else:
            return ""


class MPAdapter(BaseAdapter):
    def __init__(self):
        self.type = "MPAdapter"
        self.sheet_name = "monthly_photo_curr_article_list"
        super()

    def fetch_curr_article(self, gsession: GsheetSession) -> list[BaseArticle]:
        curr_record_list = gsession.fetch_curr_article(self.sheet_name)
        curr_article_list: list[BaseArticle] = []
        for curr_record in curr_record_list:
            if "title" not in curr_record:
                continue
            if "date" not in curr_record:
                continue
            title = curr_record["title"]
            date_str = curr_record["date"]
            date = datetime.strptime(date_str, NotifySchedule.date_format)
            curr_article_list.append(MPArticle(title=title, date=date))
        return curr_article_list

    def fetch_notify_article_list(
        self, curr_article_list: list[BaseArticle] = None
    ) -> list[BaseArticle]:
        session = ShopSession()
        news_el_list = session.fetch_schedule_list()
        article_list: list[BaseArticle] = []
        for news_el in news_el_list:
            if not isinstance(news_el, Tag):
                continue
            date = session._parse_datetime(news_el)
            title = session._parse_title(news_el)
            article_list.append(MPArticle(title=title, date=date))
        if curr_article_list is None:
            return article_list
        notify_article_list: list[BaseArticle] = self.filter_notify_article_list(
            curr_article_list, article_list
        )
        return notify_article_list

    def filter_notify_article_list(
        self, curr_article_list: list[BaseArticle], article_list: list[BaseArticle]
    ) -> list[BaseArticle]:
        start_date = self.max_date_article(curr_article_list)
        if start_date is None:
            return article_list
        title_hash_list = []
        for curr_article in curr_article_list:
            if not isinstance(curr_article, MPArticle):
                continue
            curr_article.calc_title_hash()
            title_hash_list.append(curr_article.title_hash)
        notify_article_list: list[BaseArticle] = []
        for article in article_list:
            if not isinstance(article, MPArticle):
                continue
            date = article.date
            title = article.title
            if date is None or title == "":
                continue
            print(f"{start_date=} {date=}")
            if start_date < date:
                notify_article_list.append(article)
            elif start_date == date:
                article.calc_title_hash()
                title_hash = article.title_hash
                print(f"{title_hash=} {title_hash_list=}")
                print(f"{title_hash not in title_hash_list=}")
                if title_hash not in title_hash_list:
                    notify_article_list.append(article)
        return notify_article_list

    def regist_article(
        self, article_list: list[BaseArticle], gsession: GsheetSession
    ) -> None:
        gsession.clear_schedule(self.sheet_name)
        headers = gsession.fetch_headers(self.sheet_name)
        table = []
        _article_list = self.filter_max_date_article(article_list)
        for article in _article_list:
            if not isinstance(article, MPArticle):
                continue
            article.calc_title_hash()
            row = []
            for key in headers:
                if key == "id":
                    row.append("=ROW()-1")
                else:
                    row.append(article.get(key))
            table.append(row)
        gsession.write_table(table, self.sheet_name)
