from datetime import datetime

from opime_notify.fetch_schedule import Parser, Schedule


class TestSchedule:
    def test_init(self):
        title = "test title"
        date = datetime.now()
        type = "type"
        description = "description"
        s = Schedule(title=title, date=date, type=type, description=description)
        assert s.title == title
        assert s.date == date
        assert s.type == type
        assert s.description == description

    def test_str(self):
        title = "test title"
        date = datetime.now()
        type = "type"
        description = "description"
        s = Schedule(title=title, date=date, type=type, description=description)
        assert isinstance(str(s), str)

    def test_repr(self):
        title = "test title"
        date = datetime.now()
        type = "type"
        description = "description"
        s = Schedule(title=title, date=date, type=type, description=description)
        assert isinstance(repr(s), str)

    def test_get_date_str(self):
        title = "test title"
        date = datetime.now()
        type = "type"
        description = "description"
        s = Schedule(title=title, date=date, type=type, description=description)
        assert isinstance(s.get_date_str(), str)
        s.date = None
        assert s.get_date_str() == ""


class TestParser:
    def test_init(self):
        title = "test title"
        date = datetime.now()
        type = "type"
        description = "description"
        s = Schedule(title=title, date=date, type=type, description=description)
        p = Parser(s)
        assert p.schedule == s

    def test_text_normalize(self):
        text = "　＋　"
        expect_text = "+"
        s = Schedule(title="", date=None, type="", description="")
        p = Parser(s)
        assert p._text_normalize(text) == expect_text

    def test_trim_week(self):
        text = "abcd(A)efg"
        expect_text = "abcdefg"
        s = Schedule(title="", date=None, type="", description="")
        p = Parser(s)
        assert p._trim_week_str(text) == expect_text
