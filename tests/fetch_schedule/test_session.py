from datetime import datetime

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.exceptions import HTTPError

from opime_notify.fetch_schedule import Schedule
from opime_notify.fetch_schedule.session import Session
from opime_notify.fetch_schedule.theatre_parser import TheatreSchedule


class TestFetchScheduleSession:
    def test_find_news_body(self):
        test_text = '<div class="news-block-inner">text</div>'
        s = Session()
        res = s._find_news_body(test_text)
        assert isinstance(res, Tag)
        assert res.text == "text"

    @pytest.mark.parametrize(
        "title_text,expect_tagname,expect_title",
        [
            ("<p><span>tagname</span>title</p>", "tagname", "title"),
            ("<p>title</p>", "", "title"),
            ("<p><span>tagname</span></p>", "tagname", ""),
            ("<p></p>", "", ""),
        ],
    )
    def test_split_tag_and_title(self, title_text, expect_tagname, expect_title):
        soup = BeautifulSoup(title_text, "html.parser")
        s = Session()
        tagname, title = s._split_tag_and_title(soup.p)
        assert tagname == expect_tagname
        assert title == expect_title

    @pytest.mark.parametrize(
        "date_text,expect_value",
        [
            ("<p>2021.08.23</p>", datetime(2021, 8, 23)),
            ("<p>2021.08.23 12:00:00</p>", datetime(2021, 8, 23)),
            ("<p>bad text</p>", None),
        ],
    )
    def test_parse_datetime(self, date_text, expect_value):
        soup = BeautifulSoup(date_text, "html.parser")
        s = Session()
        assert s._parse_datetime(soup.p) == expect_value

    def test_fetch_schedule_list(self, requests_mock):
        s = Session()
        test_text = f'<div class="news-block-inner"><a href="{s.NEWS_URL}/detail/test"></a></div>'  # noqa: E501
        mock_url = f"{s.NEWS_URL}/articles/1/0/0"
        requests_mock.get(mock_url, text=test_text)
        news_list = s.fetch_schedule_list(page=1, category=0)
        assert len(news_list) == 1
        assert isinstance(news_list[0], Tag)

    def test_fetch_schedule_list_error(self, requests_mock):
        s = Session()
        mock_url = f"{s.NEWS_URL}/articles/1/0/0"
        requests_mock.get(mock_url, status_code=400)
        with pytest.raises(HTTPError):
            s.fetch_schedule_list(page=1, category=0)

    def test_fetch_schedule_detail(self, requests_mock):
        mock_url = "https://www.example.com/"
        test_body = """<div class="title"><span>tagname</span>title</div>
        <div class="date">2021.08.23</div>
        <div class="content">content</div>"""
        test_text = f'<div class="news-block-inner">{test_body}</div>'
        requests_mock.get(mock_url, text=test_text)
        s = Session()
        schedule = s.fetch_schedule_detail(mock_url)
        assert isinstance(schedule, Schedule)

    def test_fetch_schedule_detail_error(self, requests_mock):
        mock_url = "https://www.example.com/"
        requests_mock.get(mock_url, status_code=400)
        s = Session()
        with pytest.raises(HTTPError):
            s.fetch_schedule_detail(mock_url)

    def test_fetch_schedule_theatre(self, monkeypatch):
        s = Session()

        def dummy_schedule_list(*args, **kwargs):
            test_text = f'<a href="{s.NEWS_URL}/detail/test"></a>'
            soup = BeautifulSoup(test_text, "html.parser")
            return soup("a")

        def dummy_schedule_detail(*args, **kwargs):
            return TheatreSchedule(
                title="title", date=datetime(2021, 8, 23), type="test"
            )

        class DummyClass:
            def __init__(self, *args, **kwargs):
                pass

            def parse(self, *args, **kwargs):
                return [
                    TheatreSchedule(
                        title="title", date=datetime(2021, 8, 23), type="test"
                    )
                ]

        s.fetch_schedule_list = dummy_schedule_list
        s.fetch_schedule_detail = dummy_schedule_detail
        monkeypatch.setattr(
            "opime_notify.fetch_schedule.session.TheatreNewsParser", DummyClass
        )
        slist = s.fetch_schedule_theatre(page=1)
        assert len(slist) == 1
        assert slist[0].title == "title"
        assert slist[0].date == datetime(2021, 8, 23)
        assert slist[0].type == "test"
