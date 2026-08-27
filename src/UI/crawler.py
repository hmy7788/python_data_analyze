"""네이버 뉴스 검색 결과를 가져오는 크롤링 모듈.

Tkinter를 전혀 알지 못한다. UI 쪽(main.py)은 이 모듈이 돌려주는 (제목, URL) 목록을
화면에 뿌리고 클릭을 연결하는 역할만 맡는다. 클래스 이름과 collect()/parse() 메서드
이름은 `미니 프로젝트 흐름도.png`가 지정한 crawler.py / DataCrawler 스펙을 따른다.
"""

import gzip
import html
import os
import re
import subprocess
import webbrowser
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# 지금은 "CNC 불량" 뉴스를 고정으로 검색한다. 이 주제 자체는 ai4i2020.csv 기반 분류
# 프로젝트와는 별개로, 나중에 크롤링 단계를 다시 다룰 때 확장할 대상이다.
SEARCH_WORD = "CNC 불량"
NEWS_COUNT = 5

# 크롤링 요청이 실패할 수 있는 예외들. UI 쪽에서 그대로 잡아서 에러 메시지로 보여준다.
CRAWL_ERRORS = (HTTPError, URLError, TimeoutError, RuntimeError, OSError)


class NaverNewsParser(HTMLParser):
    """네이버 뉴스 검색 페이지에서 제목과 기사 URL을 추출한다."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self._anchor_depth = 0
        self._anchor_is_news = False
        self._anchor_title = ""
        self._anchor_url = ""
        self._anchor_text = []
        self._headline_depth = 0
        self._headline_text = []
        self._headline_url = ""

    @staticmethod
    def _attrs_to_dict(attrs):
        return {key: (value or "") for key, value in attrs}

    def _add_item(self, title, url):
        title = re.sub(r"\s+", " ", html.unescape(title)).strip()
        url = html.unescape(url).strip()
        if not title or not url.startswith(("http://", "https://")):
            return
        if all(item["title"] != title for item in self.items):
            self.items.append({"title": title, "url": url})

    def handle_starttag(self, tag, attrs):
        values = self._attrs_to_dict(attrs)
        classes = values.get("class", "").split()

        # 기존 네이버 검색 결과 마크업: <a class="news_tit" ...>
        if tag == "a":
            self._anchor_depth += 1
            if self._anchor_depth == 1:
                self._anchor_is_news = "news_tit" in classes
                self._anchor_title = values.get("title", "")
                self._anchor_url = values.get("href", "")
                self._anchor_text = []

        # 신규 검색 결과 마크업의 뉴스 제목 텍스트.
        if any("text-type-headline" in class_name for class_name in classes):
            self._headline_depth = 1
            self._headline_text = []
            self._headline_url = self._anchor_url
        elif self._headline_depth:
            self._headline_depth += 1

    def handle_endtag(self, tag):
        if self._headline_depth:
            self._headline_depth -= 1
            if self._headline_depth == 0:
                self._add_item("".join(self._headline_text), self._headline_url)
                self._headline_text = []
                self._headline_url = ""

        if tag == "a" and self._anchor_depth:
            if self._anchor_depth == 1 and self._anchor_is_news:
                self._add_item(
                    self._anchor_title or "".join(self._anchor_text),
                    self._anchor_url,
                )
            self._anchor_depth -= 1
            if self._anchor_depth == 0:
                self._anchor_is_news = False
                self._anchor_url = ""

    def handle_data(self, data):
        if self._anchor_depth and self._anchor_is_news:
            self._anchor_text.append(data)
        if self._headline_depth:
            self._headline_text.append(data)


class DataCrawler:
    """네이버 뉴스에서 search_word 관련 기사를 최대 count개 수집한다."""

    def __init__(self, search_word=SEARCH_WORD, count=NEWS_COUNT):
        self.search_word = search_word
        self.count = count

    def _build_url(self):
        return (
            "https://search.naver.com/search.naver"
            f"?where=news&query={quote(self.search_word)}&sort=0"
        )

    def collect(self):
        """네이버 뉴스 검색 결과 페이지를 요청해 HTML 원문을 가져온다."""
        # 실제 브라우저와 유사한 헤더를 사용해 네이버 검색 페이지를 요청한다.
        request = Request(
            self._build_url(),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
                "Accept-Encoding": "gzip",
                "Referer": "https://www.naver.com/",
            },
        )

        with urlopen(request, timeout=12) as response:
            body = response.read()
            if response.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            charset = response.headers.get_content_charset() or "utf-8"
            return body.decode(charset, errors="replace")

    def parse(self, page_html):
        """HTML에서 기사 제목/링크를 추출해 최대 count개까지 반환한다."""
        parser = NaverNewsParser()
        parser.feed(page_html)

        if not parser.items:
            raise RuntimeError("네이버 검색 결과에서 뉴스 제목과 링크를 찾지 못했습니다.")
        return parser.items[: self.count]

    def fetch_news_items(self):
        """collect()로 페이지를 받아 parse()로 (제목, URL) 목록을 뽑아낸다."""
        return self.parse(self.collect())


def open_in_chrome(url):
    """설치된 Chrome을 우선 사용하고, 없으면 기본 브라우저로 연다."""
    chrome_candidates = []
    locations = (
        ("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"),
        ("PROGRAMFILES(X86)", "Google/Chrome/Application/chrome.exe"),
        ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe"),
    )
    for environment_name, relative_path in locations:
        base_path = os.environ.get(environment_name)
        if base_path:
            chrome_candidates.append(Path(base_path) / relative_path)

    for chrome_path in chrome_candidates:
        if chrome_path.is_file():
            subprocess.Popen([str(chrome_path), url])
            return
    webbrowser.open_new_tab(url)
