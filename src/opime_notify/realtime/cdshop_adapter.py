from datetime import datetime
from typing import Optional

from opime_notify.fetch_schedule.session import CDShopSession
from opime_notify.gsheet import GsheetSession
from opime_notify.realtime import BaseAdapter, BaseArticle
from opime_notify.schedule import NotifySchedule


class CDShopArticle(BaseArticle):
    def __init__(self, title: str = "", date: Optional[datetime] = None):
        self.title = title
        self.date = date
        self.type = "CDShopArticle"

    def __str__(self):
        return f"{self.type=} {self.title=}, {self.date=}"

    def __repr__(self):
        return f"{self.type}({repr(self.title)}, {repr(self.date)})"

    def get_notify_list(self) -> list[NotifySchedule]:
        title = "【新着CDショップ情報】"
        description = f"""NGT48オフィシャルCDショップの新着記事が更新されました。
[{self.title}]
        """
        url = "https://ngt48cd.shop/news/list"
        date_str = datetime.now().strftime(NotifySchedule.date_format)
        notify = NotifySchedule(
            id=0,
            title=title,
            date=date_str,
            description=description,
            url=url,
            status="REALTIME",
        )
        return [notify]

    def get(self, key) -> str:
        if key == "title":
            return self.title
        elif key == "date":
            if self.date is None:
                return ""
            return self.date.strftime(NotifySchedule.date_format)
        else:
            return ""


class CDShopAdapter(BaseAdapter):
    def __init__(self):
        self.type = "CDShopAdapter"
        self.sheet_name = "cdshop_curr_article_list"
        super()

    def convert_resdict_to_article(self, resdict: dict) -> Optional[BaseArticle]:
        if "title" not in resdict:
            return None
        if "date" not in resdict:
            return None
        if "published" not in resdict["date"]:
            return None
        title = resdict["title"]
        # {"date": {"published": "2022-12-05T00:00:00+09:00"}}
        datestr = resdict["date"]["published"]
        date = datetime.fromisoformat(datestr)
        # aware -> native
        date = date.replace(tzinfo=None)
        return CDShopArticle(title=title, date=date)

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
            curr_article_list.append(CDShopArticle(title=title, date=date))

        return curr_article_list

    def fetch_notify_article_list(
        self, curr_article_list: list[BaseArticle] = None
    ) -> list[BaseArticle]:
        session = CDShopSession()
        _article_list: list[Optional[BaseArticle]] = [
            self.convert_resdict_to_article(a) for a in session.fetch_article_list()
        ]
        article_list: list[BaseArticle] = [a for a in _article_list if a is not None]
        if curr_article_list is None:
            return article_list
        notify_article_list: list[BaseArticle] = self.filter_notify_article_list(
            curr_article_list, article_list
        )
        return notify_article_list

    def filter_notify_article_list(
        self, curr_article_list: list[BaseArticle], article_list: list[BaseArticle]
    ) -> list[BaseArticle]:
        max_date = self.get_max_date(curr_article_list)
        if len(curr_article_list) < 1 or max_date is None:
            return article_list
        notify_article_list: list[BaseArticle] = []
        for article in article_list:
            if not isinstance(article, CDShopArticle):
                continue
            if article.date is None or article.title == "":
                continue
            if max_date < article.date:
                notify_article_list.append(article)
        return notify_article_list

    def filter_max_date_article(
        self, article_list: list[BaseArticle]
    ) -> list[BaseArticle]:
        max_date = self.get_max_date(article_list)
        max_date_article_list: list[BaseArticle] = []
        for article in article_list:
            if isinstance(article, CDShopArticle):
                if article.date == max_date:
                    max_date_article_list.append(article)
        return max_date_article_list

    def get_max_date(self, article_list: list[BaseArticle]) -> Optional[datetime]:
        _article_list = [a for a in article_list if isinstance(a, CDShopArticle)]
        if len(_article_list) == 0:
            return None
        return max([a.date for a in _article_list if a.date is not None])

    def regist_article(
        self, article_list: list[BaseArticle], gsession: GsheetSession
    ) -> None:
        gsession.clear_schedule(self.sheet_name)
        headers = gsession.fetch_headers(self.sheet_name)
        table = []
        _article_list = self.filter_max_date_article(article_list)
        for article in _article_list:
            if not isinstance(article, CDShopArticle):
                continue
            row = []
            for key in headers:
                row.append(article.get(key))
            table.append(row)
        gsession.write_table(table, self.sheet_name)
