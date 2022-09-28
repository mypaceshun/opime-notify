import re
from datetime import datetime
from typing import Optional

from opime_notify.fetch_schedule.session import ShopSession, TagDict
from opime_notify.gsheet import GsheetSession
from opime_notify.realtime import BaseAdapter, BaseArticle
from opime_notify.schedule import NotifySchedule


class MPArticle(BaseArticle):
    def __init__(
        self,
        title: str = "",
        date: Optional[datetime] = None,
        code: str = "",
        id: int = -1,
        name: str = "",
        name_kana: str = "",
    ):
        self.type = "MPArticle"
        self.title = title
        self.date = date
        self.code = code
        self.id = id
        self.name = name
        self.name_kana = name_kana

    def __str__(self):
        return f"{self.type=} {self.title=}, {self.date=}"

    def __repr__(self):
        return f"{self.type}({repr(self.title)}, {repr(self.date)})"

    def get(self, key) -> str:
        if key == "title":
            return self.title
        elif key == "date":
            if self.date is None:
                return ""
            return self.date.strftime(NotifySchedule.date_format)
        elif key == "id":
            return str(self.id)
        elif key == "code":
            return self.code
        elif key == "name":
            return self.name
        elif key == "name_kana":
            return self.name_kana
        else:
            return ""

    def get_notify_list(self) -> list[NotifySchedule]:
        title = f"【新着ショップ情報】{self.name}"
        description = f"""NGT48オフィシャルショップにて月別生写真が新発売されている可能性があります。
[{self.name}]"""
        url = "https://official-goods-store.jp/ngt48/product/list?tag_codes=NGT-T-003%252C{self.code}"  # noqa: E501
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


class MPAdapter(BaseAdapter):
    def __init__(self):
        self.type = "MPAdapter"
        self.sheet_name = "monthly_photo_curr_tag_list"
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
            id = int(curr_record["id"])
            code = curr_record["code"]
            name = curr_record["name"]
            name_kana = curr_record["name_kana"]
            date = datetime.strptime(date_str, NotifySchedule.date_format)
            curr_article_list.append(
                MPArticle(
                    title=title,
                    date=date,
                    code=code,
                    id=id,
                    name=name,
                    name_kana=name_kana,
                )
            )
        return curr_article_list

    def fetch_notify_article_list(
        self, curr_article_list: list[BaseArticle] = None
    ) -> list[BaseArticle]:
        # mpadapterで取得するのは記事ではないが、互換性のために記事のように保存する
        session = ShopSession()
        tag_list = session.fetch_tag_list()
        tag_list = self.filter_mptags(tag_list)
        date = datetime.now()
        article_list: list[BaseArticle] = []
        for tag in tag_list:
            title = session.generate_title(tag["code"], tag["name"])
            article_list.append(
                MPArticle(
                    title=title,
                    date=date,
                    code=tag["code"],
                    id=tag["id"],
                    name=tag["name"],
                    name_kana=tag["name_kana"],
                )
            )
        if curr_article_list is None:
            return article_list
        notify_article_list: list[BaseArticle] = self.filter_notify_article_list(
            curr_article_list, article_list
        )
        return notify_article_list

    def filter_notify_article_list(
        self, curr_article_list: list[BaseArticle], article_list: list[BaseArticle]
    ) -> list[BaseArticle]:
        # idは加算され続けていいくことが前提
        max_id = self.get_max_id(curr_article_list)
        if len(curr_article_list) < 1:
            return article_list
        code_list: list[str] = []
        for curr_article in curr_article_list:
            if not isinstance(curr_article, MPArticle):
                continue
            code_list.append(curr_article.code)
        notify_article_list: list[BaseArticle] = []
        for article in article_list:
            if not isinstance(article, MPArticle):
                continue
            date = article.date
            title = article.title
            id = article.id
            if date is None or title == "":
                continue
            if max_id < id:
                notify_article_list.append(article)
        return notify_article_list

    def get_max_id(self, article_list: list[BaseArticle]) -> int:
        _article_list = [a for a in article_list if isinstance(a, MPArticle)]
        if len(_article_list) == 0:
            return 0
        return max([a.id for a in _article_list])

    def filter_max_date_article(
        self, article_list: list[BaseArticle]
    ) -> list[BaseArticle]:
        max_id = self.get_max_id(article_list)
        max_id_article_list: list[BaseArticle] = []
        for article in article_list:
            if isinstance(article, MPArticle):
                if article.id == max_id:
                    max_id_article_list.append(article)
        return max_id_article_list

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
            row = []
            for key in headers:
                row.append(article.get(key))
            table.append(row)
        gsession.write_table(table, self.sheet_name)

    def filter_mptags(self, tags: list[TagDict]) -> list[TagDict]:
        mppattern = r"\d{4}年\d{1,2}月度個別生写真"
        mpp = re.compile(mppattern)
        mptaglist: list[TagDict] = []
        for tag in tags:
            m = mpp.match(tag["name"])
            if m:
                mptaglist.append(tag)
        return mptaglist
