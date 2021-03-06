from datetime import datetime

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.exceptions import HTTPError

from opime_notify.fetch_schedule import Schedule
from opime_notify.fetch_schedule.session import OfficialSession, ShopSession
from opime_notify.fetch_schedule.theatre_parser import TheatreSchedule


class TestOfficialSession:
    def test_find_news_body(self):
        test_text = '<div class="news-block-inner">text</div>'
        s = OfficialSession()
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
        s = OfficialSession()
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
        s = OfficialSession()
        assert s._parse_datetime(soup.p) == expect_value

    def test_fetch_schedule_list(self, requests_mock):
        s = OfficialSession()
        test_text = f'<div class="news-block-inner"><a href="{s.NEWS_URL}/detail/test"></a></div>'  # noqa: E501
        mock_url = f"{s.NEWS_URL}/articles/1/0/0"
        requests_mock.get(mock_url, text=test_text)
        news_list = s.fetch_schedule_list(page=1, category=0)
        assert len(news_list) == 1
        assert isinstance(news_list[0], Tag)

    def test_fetch_schedule_list_error(self, requests_mock):
        s = OfficialSession()
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
        s = OfficialSession()
        schedule = s.fetch_schedule_detail(mock_url)
        assert isinstance(schedule, Schedule)

    def test_fetch_schedule_detail_error(self, requests_mock):
        mock_url = "https://www.example.com/"
        requests_mock.get(mock_url, status_code=400)
        s = OfficialSession()
        with pytest.raises(HTTPError):
            s.fetch_schedule_detail(mock_url)

    def test_fetch_schedule_theatre(self, monkeypatch):
        s = OfficialSession()

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
                    Schedule(title="title", date=datetime(2021, 8, 23), type="test")
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

    def test_fetch_schedule_otsale(self, monkeypatch):
        s = OfficialSession()

        def dummy_schedule_list(*args, **kwargs):
            test_text = f"""<a href="{s.NEWS_URL}/detail/test">
<div class="title"><span class="badge">Badge</span>
???????????? ???????????????1?????????99???????????????????????????????????????</div></a>"""
            soup = BeautifulSoup(test_text, "html.parser")
            return soup("a")

        def dummy_schedule_detail(*args, **kwargs):
            return Schedule(title="title", date=datetime(2021, 8, 23), type="test")

        class DummyClass:
            def __init__(self, *args, **kwargs):
                pass

            def parse(self, *args, **kwargs):
                return [
                    Schedule(title="title", date=datetime(2021, 8, 23), type="test")
                ]

        s.fetch_schedule_list = dummy_schedule_list
        s.fetch_schedule_detail = dummy_schedule_detail
        monkeypatch.setattr(
            "opime_notify.fetch_schedule.session.OTSaleNewsParser", DummyClass
        )
        slist = s.fetch_schedule_otsale()
        assert len(slist) == 1
        assert slist[0].title == "title"
        assert slist[0].date == datetime(2021, 8, 23)
        assert slist[0].type == "test"


class TestShopSession:
    def test_find_news_body(self):
        s = ShopSession()
        text = '<div class="entry-content"></div>'
        res = s._find_news_body(text)
        assert isinstance(res, Tag)

    def test_find_news_title(self):
        s = ShopSession()
        text = '<div class="news-item"></div>'
        res = s._find_news_title(text)
        assert isinstance(res, Tag)

    @pytest.mark.parametrize(
        "text,expect",
        [
            ("<p></p>", None),
            ('<p><div class="block-1"></div></p>', None),
            ('<p><div class="block-1">1997.08.23</div></p>', datetime(1997, 8, 23)),
        ],
    )
    def test_parse_datetime(self, text, expect):
        s = ShopSession()
        soup = BeautifulSoup(text, "html.parser")
        news_el = soup.p
        assert s._parse_datetime(news_el) == expect

    @pytest.mark.parametrize(
        "text,expect",
        [
            ("<p></p>", ""),
            ('<p><div class="category"></div></p>', ""),
            ('<p><div class="category"> test </div></p>', "test"),
        ],
    )
    def test_parse_category(self, text, expect):
        s = ShopSession()
        soup = BeautifulSoup(text, "html.parser")
        news_el = soup.p
        assert s._parse_category(news_el) == expect

    @pytest.mark.parametrize(
        "text,expect",
        [
            ("<p></p>", ""),
            ('<p><div class="title-post"></div></p>', ""),
            ('<p><div class="title-post"> test </div></p>', "test"),
        ],
    )
    def test_parse_title(self, text, expect):
        s = ShopSession()
        soup = BeautifulSoup(text, "html.parser")
        news_el = soup.p
        assert s._parse_title(news_el) == expect

    @pytest.mark.parametrize(
        "text,expect",
        [
            ("<p></p>", ""),
            ('<p><div class="title-post"></div></p>', ""),
            ('<p><div class="title-post"><a></a></div></p>', ""),
            ('<p><div class="title-post"><a href=" test "></a></div></p>', "test"),
        ],
    )
    def test_parse_url(self, text, expect):
        s = ShopSession()
        soup = BeautifulSoup(text, "html.parser")
        news_el = soup.p
        assert s._parse_url(news_el) == expect

    @pytest.mark.parametrize(
        "title,expect",
        [
            ("title", False),
            ("1993???8?????????????????????0????????????Vol.0", True),
        ],
    )
    def test_is_monthly_photo_title(self, title, expect):
        s = ShopSession()
        assert s.is_monthly_photo_title(title) is expect

    def test_fetch_schedule_list(self, requests_mock):
        s = ShopSession()
        test_text = '<div class="entry-content"><div class="news-item"></div></div>'  # noqa: E501
        mock_url = f"{s.NEWS_URL}page/2/"
        requests_mock.get(mock_url, text=test_text)
        news_list = s.fetch_schedule_list(page=2)
        assert len(news_list) == 1
        assert isinstance(news_list[0], Tag)

    @pytest.mark.parametrize(
        "text, expect",
        [
            ("<div></div>", None),
            ('<div class="news-item entry-content"></div>', None),
            (
                """<div class="news-item"><div class="title-post"> title </div>
            <div class="block-1">1997.08.23</div></div>
            <div class="entry-content"> test </div>""",
                Schedule("title", datetime(1997, 8, 23), "monthly_photo", "test"),
            ),
        ],
    )
    def test_fetch_schedule_detail(self, requests_mock, text, expect):
        s = ShopSession()
        mock_url = "https://localhost/"
        requests_mock.get(mock_url, text=text)
        if expect is None:
            assert s.fetch_schedule_detail(mock_url) is None
        else:
            res = s.fetch_schedule_detail(mock_url)
            assert res.title == expect.title
            assert res.date == expect.date
            assert res.type == expect.type
            assert res.description == expect.description

    def test_fetch_schedule_monthly_photo(self, monkeypatch):
        s = ShopSession()

        def dummy_fetch_list(*args, **kwargs):
            text = '<p><div class="title-post"><a href="test"></a>1993???8?????????????????????0????????????Vol.0</div></p>'  # noqa: E501
            soup = BeautifulSoup(text, "html.parser")
            return soup("p")

        def dummy_fetch_detail(*args, **kwargs):
            return Schedule("title", datetime(1997, 8, 23), "test")

        class DummyClass:
            def __init__(self, *args, **kwargs):
                pass

            def parse(self, *args, **kwargs):
                return [
                    Schedule(title="title", date=datetime(1997, 8, 23), type="test")
                ]

        s.fetch_schedule_list = dummy_fetch_list
        s.fetch_schedule_detail = dummy_fetch_detail
        monkeypatch.setattr(
            "opime_notify.fetch_schedule.session.MonthlyPhotoParser", DummyClass
        )
        slist = s.fetch_schedule_monthly_photo()
        assert len(slist) == 1
        assert slist[0].title == "title"
        assert slist[0].date == datetime(1997, 8, 23)
        assert slist[0].type == "test"
