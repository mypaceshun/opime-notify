import re
import unicodedata
from datetime import datetime
from typing import Optional


class Schedule:
    def __init__(
        self, title: str, date: Optional[datetime], type: str, description: str = ""
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

    def get_date_str(self) -> str:
        date_format = "%Y/%m/%d %H:%M:%S"
        if self.date is None:
            return ""
        return self.date.strftime(date_format)


class Parser:
    def __init__(self, schedule: Schedule):
        self.schedule = schedule

    def _text_normalize(self, text: str) -> str:
        _text = unicodedata.normalize("NFKC", text)
        _text = _text.replace(" ", "")
        return _text

    def _trim_week_str(self, text: str, after: str = "") -> str:
        return re.sub(r"\(.\)", after, text)
