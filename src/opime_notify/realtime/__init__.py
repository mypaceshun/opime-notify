from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from opime_notify.gsheet import GsheetSession
from opime_notify.schedule import NotifySchedule


class BaseArticle(ABC):
    def __init__(self):
        self.type = "BaseArticle"
        self.title: str = ""
        self.date: Optional[datetime] = None

    def __str__(self):
        return f"{self.type=}"

    def __repr__(self):
        return f"{self.type}()"

    @abstractmethod
    def get_notify_list(self) -> list[NotifySchedule]:
        return []


class BaseAdapter(ABC):
    def __init__(self):
        self.type = "BaseAdapter"

    def __str__(self):
        return f"{self.type=}"

    def __repr__(self):
        return f"{self.type}()"

    def fetch_curr_article(self, gsession: GsheetSession) -> list[BaseArticle]:
        return []

    @abstractmethod
    def fetch_notify_article_list(
        self, curr_article_list: list[BaseArticle] = None
    ) -> list[BaseArticle]:
        return []

    def regist_article(
        self, article_list: list[BaseArticle], gsession: GsheetSession
    ) -> None:
        return None

    def max_date_article(self, article_list: list[BaseArticle]) -> Optional[datetime]:
        if len(article_list) == 0:
            return None
        date_list = [a.date for a in article_list if a.date is not None]
        if len(date_list) == 0:
            return None
        return max(date_list)

    def filter_max_date_article(
        self, article_list: list[BaseArticle]
    ) -> list[BaseArticle]:
        max_date = self.max_date_article(article_list)
        if max_date is None:
            return []
        return [a for a in article_list if a.date is not None and a.date == max_date]
