import gzip
import html
import os
import re
import subprocess
import threading
import tkinter as tk
import webbrowser
from html.parser import HTMLParser
from pathlib import Path
from tkinter import ttk
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


SEARCH_WORD = "CNC 불량"
NEWS_COUNT = 5
# 왼쪽 입력칸의 화면 배치 순서이자 모델에 전달할 변수명이다.
MODEL_INPUT_NAMES = (
    "type",
    "air_temp",
    "proc_temp",
    "rot_speed",
    "torque",
    "tool_wear",
)
NAVER_NEWS_URL = (
    "https://search.naver.com/search.naver"
    f"?where=news&query={quote(SEARCH_WORD)}&sort=0"
)


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


def fetch_news_items():
    """네이버 뉴스 검색 결과에서 제목과 링크를 최대 NEWS_COUNT개 가져온다."""
    # 실제 브라우저와 유사한 헤더를 사용해 네이버 검색 페이지를 요청한다.
    request = Request(
        NAVER_NEWS_URL,
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
        page = body.decode(charset, errors="replace")

    parser = NaverNewsParser()
    parser.feed(page)

    if not parser.items:
        raise RuntimeError("네이버 검색 결과에서 뉴스 제목과 링크를 찾지 못했습니다.")
    return parser.items[:NEWS_COUNT]


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


class NewsDashboard(tk.Tk):
    """왼쪽 모델 입력 화면과 오른쪽 뉴스 화면을 관리하는 메인 UI."""

    # UI 전체에서 공통으로 사용하는 색상이다.
    BG = "#F3F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17202A"
    SUBTEXT = "#667085"
    GREEN = "#03C75A"
    BORDER = "#E4E7EC"

    def __init__(self):
        super().__init__()
        self.title("CNC 불량 뉴스 모니터")
        self.geometry("1280x680")
        self.minsize(1000, 560)
        self.configure(bg=self.BG)

        self.status_var = tk.StringVar(value="뉴스를 불러오는 중입니다...")
        self.cards = []
        self.nav_buttons = []
        self.filter_inputs = []

        # 각 Entry의 현재 값을 보관한다. UI 입력과 모델 변수를 연결하는 역할이다.
        self.model_input_vars = {
            name: tk.StringVar(value="") for name in MODEL_INPUT_NAMES
        }
        self.model_input_values = {name: "" for name in MODEL_INPUT_NAMES}

        # Data 모델링 코드에서 self.air_temp처럼 직접 접근할 수도 있게 초기화한다.
        for name in MODEL_INPUT_NAMES:
            setattr(self, name, "")

        self._build_ui()
        # 첫 번째 버튼이 기본 선택 상태이므로 시작 화면에도 안내 문구를 표시한다.
        self._show_all_data_view()
        self.after(150, self.refresh_news)

    def _build_ui(self):
        # 버튼별 기본/선택 상태 디자인을 정의한다.
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Refresh.TButton",
            font=("맑은 고딕", 10, "bold"),
            foreground="#FFFFFF",
            background=self.GREEN,
            borderwidth=0,
            padding=(14, 9),
        )
        style.map(
            "Refresh.TButton",
            background=[("active", "#02AE4F"), ("disabled", "#A7E6C2")],
        )
        style.configure(
            "Nav.TButton",
            font=("맑은 고딕", 9, "bold"),
            foreground="#475467",
            background="#F2F4F7",
            borderwidth=0,
            padding=(8, 12),
        )
        style.map(
            "Nav.TButton",
            foreground=[("active", self.TEXT)],
            background=[("active", "#E4E7EC")],
        )
        style.configure(
            "NavActive.TButton",
            font=("맑은 고딕", 9, "bold"),
            foreground="#FFFFFF",
            background=self.GREEN,
            borderwidth=0,
            padding=(8, 12),
        )
        style.map(
            "NavActive.TButton",
            foreground=[("active", "#FFFFFF")],
            background=[("active", "#02AE4F")],
        )

        # 메인 창을 동일한 크기의 왼쪽/오른쪽 영역으로 나눈다.
        split = tk.Frame(self, bg=self.BORDER)
        split.pack(fill="both", expand=True)
        split.grid_rowconfigure(0, weight=1)
        split.grid_columnconfigure(0, weight=1, uniform="half")
        split.grid_columnconfigure(1, weight=1, uniform="half")

        # 왼쪽은 요청대로 비어 있는 흰색 페이지다.
        # ---------------- 왼쪽: 모델 데이터 영역 ----------------
        left_page = tk.Frame(split, bg="#FFFFFF")
        left_page.grid(row=0, column=0, sticky="nsew", padx=(0, 1))

        left_content = tk.Frame(left_page, bg="#FFFFFF")
        left_content.pack(fill="both", expand=True, padx=28, pady=30)

        navigation = tk.Frame(left_content, bg="#FFFFFF")
        navigation.pack(fill="x")
        for column in range(3):
            navigation.grid_columnconfigure(column, weight=1, uniform="navigation")

        navigation_labels = (
            "전체 데이터 한 눈에 보기",
            "모델 훈련 결과 보기",
            "모델 입력하기",
        )
        for index, label in enumerate(navigation_labels):
            button = ttk.Button(
                navigation,
                text=label,
                style="NavActive.TButton" if index == 0 else "Nav.TButton",
                command=lambda selected=index: self._select_left_view(selected),
            )
            button.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=(0 if index == 0 else 5, 0 if index == 2 else 5),
            )
            self.nav_buttons.append(button)

        # MODEL_INPUT_NAMES의 순서대로 라벨과 입력칸 6개를 생성한다.
        input_row = tk.Frame(left_content, bg="#FFFFFF")
        input_row.pack(fill="x", pady=(14, 22))
        for column, variable_name in enumerate(MODEL_INPUT_NAMES):
            input_row.grid_columnconfigure(column, weight=1, uniform="inputs")

            input_group = tk.Frame(input_row, bg="#FFFFFF")
            input_group.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(0 if column == 0 else 4, 0 if column == 5 else 4),
            )

            tk.Label(
                input_group,
                text=variable_name,
                font=("Arial", 8),
                fg=self.SUBTEXT,
                bg="#FFFFFF",
            ).pack(anchor="w", pady=(0, 4))

            input_field = ttk.Entry(
                input_group,
                textvariable=self.model_input_vars[variable_name],
                font=("맑은 고딕", 10),
            )
            input_field.pack(fill="x", ipady=6)
            self.filter_inputs.append(input_field)

        # 선택한 메뉴의 데이터를 표시할 공간. 현재는 요청대로 비워 둔다.
        self.data_box = tk.Frame(
            left_content,
            bg="#FAFBFC",
            highlightbackground=self.BORDER,
            highlightcolor=self.BORDER,
            highlightthickness=1,
        )
        self.data_box.pack(fill="both", expand=True)

        # ---------------- 오른쪽: 네이버 뉴스 영역 ----------------
        right_page = tk.Frame(split, bg=self.BG)
        right_page.grid(row=0, column=1, sticky="nsew")

        content = tk.Frame(right_page, bg=self.BG)
        content.pack(fill="both", expand=True, padx=42, pady=40)

        top = tk.Frame(content, bg=self.BG)
        top.pack(fill="x")

        title_group = tk.Frame(top, bg=self.BG)
        title_group.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_group,
            text="데이터 크롤링",
            font=("맑은 고딕", 21, "bold"),
            fg=self.TEXT,
            bg=self.BG,
        ).pack(anchor="w")
        tk.Label(
            title_group,
            text=f"네이버 뉴스 검색  ·  {SEARCH_WORD}",
            font=("맑은 고딕", 10),
            fg=self.SUBTEXT,
            bg=self.BG,
            pady=6,
        ).pack(anchor="w")

        self.refresh_button = ttk.Button(
            top,
            text="새로고침",
            style="Refresh.TButton",
            command=self.refresh_news,
        )
        self.refresh_button.pack(side="right", padx=(12, 0))

        tk.Frame(content, height=1, bg=self.BORDER).pack(fill="x", pady=(18, 24))

        for number in range(1, NEWS_COUNT + 1):
            card = self._create_news_card(content, number)
            card["frame"].pack(fill="x", pady=(0, 14))
            self.cards.append(card)

        tk.Label(
            content,
            textvariable=self.status_var,
            font=("맑은 고딕", 9),
            fg=self.SUBTEXT,
            bg=self.BG,
            wraplength=500,
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

    def _select_left_view(self, selected_index):
        """선택된 메뉴의 색상을 바꾸고 모델 입력 메뉴라면 값을 저장한다."""
        for index, button in enumerate(self.nav_buttons):
            button.configure(
                style="NavActive.TButton" if index == selected_index else "Nav.TButton"
            )

        # 각 버튼에 대응하는 데이터 박스 처리 함수를 호출한다.
        if selected_index == 0:
            self._show_all_data_view()
        elif selected_index == 1:
            self._show_training_result_view()
        elif selected_index == 2:
            # 세 번째 '모델 입력하기' 버튼을 누른 시점의 Entry 값들을 저장한다.
            self._save_model_inputs()

    def _clear_data_box(self):
        """메뉴를 전환하기 전에 데이터 박스에 표시된 기존 내용을 지운다."""
        for widget in self.data_box.winfo_children():
            widget.destroy()

    def _show_all_data_view(self):
        """'전체 데이터 한 눈에 보기' 버튼의 데이터 박스 화면을 구성한다."""
        self._clear_data_box()

        # [전체 데이터 화면 연결 위치]
        # 추후 전체 데이터를 표시할 표나 그래프로 아래 안내 문구를 교체하면 된다.
        # 생성한 위젯의 부모는 self.data_box로 지정한다.
        tk.Label(
            self.data_box,
            text="여기에 데이터를 보여주세요",
            font=("맑은 고딕", 15, "bold"),
            fg=self.SUBTEXT,
            bg="#FAFBFC",
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _show_training_result_view(self):
        """'모델 훈련 결과 보기' 버튼의 데이터 박스 화면을 구성한다."""
        self._clear_data_box()

        # [모델 훈련 결과 화면 연결 위치]
        # 추후 정확도, 손실값, 혼동행렬, 훈련 그래프로 안내 문구를 교체하면 된다.
        # 생성한 위젯의 부모는 self.data_box로 지정한다.
        tk.Label(
            self.data_box,
            text="여기에 훈련 결과를 보여주세요",
            font=("맑은 고딕", 15, "bold"),
            fg=self.SUBTEXT,
            bg="#FAFBFC",
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _save_model_inputs(self):
        """6개 Entry 값을 이름에 맞춰 모델 입력 변수로 저장한다."""
        self.model_input_values = {
            name: self.model_input_vars[name].get().strip()
            for name in MODEL_INPUT_NAMES
        }

        # self.type, self.air_temp, ... 형태의 개별 변수에도 같은 값을 넣는다.
        for name, value in self.model_input_values.items():
            setattr(self, name, value)

        self._show_model_input_view(self.model_input_values)
        self._on_model_input_saved(self.model_input_values.copy())

    def _show_model_input_view(self, values):
        """저장된 모델 입력값 6개를 데이터 박스에 표시한다."""
        self._clear_data_box()

        result_area = tk.Frame(self.data_box, bg="#FAFBFC")
        result_area.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            result_area,
            text="입력된 모델 데이터",
            font=("맑은 고딕", 15, "bold"),
            fg=self.TEXT,
            bg="#FAFBFC",
        ).grid(row=0, column=0, columnspan=2, pady=(0, 18))

        # 변수명과 입력값을 한 행씩 나란히 표시한다.
        for row, name in enumerate(MODEL_INPUT_NAMES, start=1):
            tk.Label(
                result_area,
                text=name,
                font=("Arial", 10, "bold"),
                fg=self.SUBTEXT,
                bg="#FAFBFC",
                width=13,
                anchor="e",
            ).grid(row=row, column=0, sticky="e", padx=(0, 16), pady=4)
            tk.Label(
                result_area,
                text=values[name] or "(입력 없음)",
                font=("맑은 고딕", 11),
                fg=self.TEXT,
                bg="#FAFBFC",
                width=18,
                anchor="w",
            ).grid(row=row, column=1, sticky="w", pady=4)

    def _on_model_input_saved(self, values):
        """Data 모델링 팀이 예측 함수 호출 코드를 연결할 위치다."""
        # 예: prediction = model.predict([[values["air_temp"], ...]])
        # 현재는 연결 여부를 쉽게 확인할 수 있도록 콘솔에 값만 출력한다.
        print("모델 입력값:", values)

    def _create_news_card(self, parent, number):
        """뉴스 제목 한 건을 표시할 카드 UI를 만든다."""
        outer = tk.Frame(parent, bg=self.BORDER, padx=1, pady=1)
        inner = tk.Frame(outer, bg=self.CARD, padx=20, pady=17)
        inner.pack(fill="both", expand=True)

        badge = tk.Label(
            inner,
            text=f"{number:02d}",
            font=("Arial", 10, "bold"),
            fg=self.GREEN,
            bg="#EAFBF2",
            width=3,
            padx=6,
            pady=5,
        )
        badge.pack(side="left", padx=(0, 15))

        title = tk.Label(
            inner,
            text="불러오는 중...",
            font=("맑은 고딕", 11, "bold"),
            fg=self.TEXT,
            bg=self.CARD,
            anchor="w",
            justify="left",
            wraplength=430,
            cursor="arrow",
        )
        title.pack(side="left", fill="x", expand=True)
        return {"frame": outer, "title": title}

    def refresh_news(self):
        """UI 멈춤을 방지하기 위해 별도 스레드에서 뉴스를 다시 가져온다."""
        self.refresh_button.state(["disabled"])
        self.status_var.set("네이버에서 최신 검색 결과를 불러오는 중입니다...")
        for card in self.cards:
            card["title"].unbind("<Button-1>")
            card["title"].configure(
                text="불러오는 중...", fg=self.SUBTEXT, cursor="arrow"
            )
        threading.Thread(target=self._load_news_worker, daemon=True).start()

    def _load_news_worker(self):
        """뉴스 크롤링 결과를 메인 UI 스레드에 전달한다."""
        try:
            news_items = fetch_news_items()
            self.after(0, self._show_news, news_items)
        except (HTTPError, URLError, TimeoutError, RuntimeError, OSError) as error:
            self.after(0, self._show_error, str(error))

    def _show_news(self, news_items):
        """크롤링한 제목을 카드에 표시하고 클릭 링크를 연결한다."""
        for index, card in enumerate(self.cards):
            card["title"].unbind("<Button-1>")
            if index < len(news_items):
                item = news_items[index]
                card["title"].configure(
                    text=item["title"], fg="#175CD3", cursor="hand2"
                )
                card["title"].bind(
                    "<Button-1>",
                    lambda _event, url=item["url"]: open_in_chrome(url),
                )
            else:
                card["title"].configure(
                    text="검색 결과가 없습니다.", fg=self.SUBTEXT, cursor="arrow"
                )
        self.status_var.set(
            f"네이버 뉴스 검색 결과 {len(news_items)}건 · 제목을 누르면 기사로 이동합니다."
        )
        self.refresh_button.state(["!disabled"])

    def _show_error(self, message):
        """네트워크 또는 파싱 실패 내용을 사용자에게 표시한다."""
        for card in self.cards:
            card["title"].unbind("<Button-1>")
            card["title"].configure(
                text="뉴스를 불러오지 못했습니다.", fg="#B42318", cursor="arrow"
            )
        self.status_var.set(
            "인터넷 연결 또는 네이버 응답을 확인한 뒤 새로고침해 주세요. "
            f"({message})"
        )
        self.refresh_button.state(["!disabled"])


if __name__ == "__main__":
    app = NewsDashboard()
    app.mainloop()