import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from crawler import CRAWL_ERRORS, NEWS_COUNT, DataCrawler, open_in_chrome
from visualizer import STATUS_CRITICAL, STATUS_GOOD, Visualizer


# CNC 설비 정상/불량 판별에 쓸 원본 데이터. main.py와 같은 폴더에 있다고 가정한다.
DATA_PATH = Path(__file__).resolve().parent / "ai4i2020.csv"
# 왼쪽 입력칸의 화면 배치 순서이자 모델에 전달할 변수명이다.
MODEL_INPUT_NAMES = (
    "type",
    "air_temp",
    "proc_temp",
    "rot_speed",
    "torque",
    "tool_wear",
)


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
        # 오른쪽 뉴스 패널이 사용하는 크롤러. 검색어/개수를 바꾸려면 이 인스턴스를 건드리면 된다.
        self._crawler = DataCrawler()
        # 오른쪽 패널 부제목. 그래프 카드를 클릭하면 그 차트의 검색 키워드로 바뀐다.
        self.news_subtitle_var = tk.StringVar(
            value=f"네이버 뉴스 검색  ·  {self._crawler.search_word} (기본)"
        )
        # ai4i2020.csv를 매번 다시 읽지 않도록 최초 1회만 로드해 캐시한다.
        self._dataset = None
        # 그래프 클릭 시 뜨는 설명 툴팁(Toplevel)과, 그 툴팁을 연 카드 위젯.
        self._chart_tooltip = None
        self._chart_tooltip_source = None

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
            textvariable=self.news_subtitle_var,
            font=("맑은 고딕", 10),
            fg=self.SUBTEXT,
            bg=self.BG,
            pady=6,
        ).pack(anchor="w")
        tk.Label(
            title_group,
            text="왼쪽 그래프 카드를 클릭하면 그 인사이트와 관련된 뉴스로 바뀝니다.",
            font=("맑은 고딕", 9),
            fg=self.SUBTEXT,
            bg=self.BG,
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

        # 그래프 카드가 아닌 곳을 클릭하면 열려 있는 설명 툴팁을 닫는다. 카드 쪽 클릭 핸들러가
        # "break"를 반환해 자기 자신의 토글 동작에는 이 바인딩이 끼어들지 않는다.
        self.bind("<Button-1>", lambda _event: self._close_chart_tooltip(), add="+")

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
        self._close_chart_tooltip()
        for widget in self.data_box.winfo_children():
            widget.destroy()

    def _load_dataset(self):
        """ai4i2020.csv를 읽어 캐시한다. 컬럼명/Type 값의 앞뒤 공백을 제거한다."""
        if self._dataset is None:
            dataset = pd.read_csv(DATA_PATH)
            dataset.columns = [column.strip() for column in dataset.columns]
            dataset["Type"] = dataset["Type"].str.strip()
            self._dataset = dataset
        return self._dataset

    def _show_all_data_view(self):
        """'전체 데이터 한 눈에 보기' 버튼의 데이터 박스 화면을 구성한다."""
        self._clear_data_box()

        try:
            dataset = self._load_dataset()
        except (OSError, pd.errors.ParserError, KeyError) as error:
            self._show_data_error(str(error))
            return

        scroll_area = self._make_scrollable(self.data_box)

        tk.Label(
            scroll_area,
            text=f"AI4I 2020 데이터셋 · {len(dataset):,}행 · {len(dataset.columns)}열 · 설비 정상/불량 판별용",
            font=("맑은 고딕", 10, "bold"),
            fg=self.TEXT,
            bg="#FAFBFC",
        ).pack(anchor="w", padx=12, pady=(12, 0))

        visualizer = Visualizer(dataset)
        self._build_stat_tiles(scroll_area, visualizer.summarize_status())
        self._build_chart_grid(scroll_area, visualizer.chart_specs())

    def _show_data_error(self, message):
        """CSV 로드 실패 시 데이터 박스에 원인을 표시한다."""
        tk.Label(
            self.data_box,
            text=f"데이터를 불러오지 못했습니다.\n({message})",
            font=("맑은 고딕", 11),
            fg="#B42318",
            bg="#FAFBFC",
            justify="center",
            wraplength=420,
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _make_scrollable(self, parent):
        """parent를 세로 스크롤 가능한 영역으로 감싸고, 내용을 담을 내부 Frame을 반환한다."""
        container = tk.Frame(parent, bg="#FAFBFC")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#FAFBFC", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#FAFBFC")

        inner.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfig(window_id, width=event.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 마우스가 그래프 영역 위에 있을 때만 휠 스크롤을 연결해 다른 위젯에 영향을 주지 않는다.
        def _on_wheel(event):
            # 스크롤하면 열려 있던 툴팁이 카드와 어긋나 보이므로 같이 닫는다.
            self._close_chart_tooltip()
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Destroy>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        return inner

    def _build_stat_tiles(self, parent, summary):
        """전체 건수/정상/불량/불량률 요약 카드 4개를 만든다. summary는 Visualizer.summarize_status()의 결과."""
        tiles = (
            ("전체 데이터", f"{summary['total']:,}건", self.TEXT),
            ("정상", f"{summary['normal']:,}건", STATUS_GOOD),
            ("불량", f"{summary['failure']:,}건", STATUS_CRITICAL),
            ("불량률", f"{summary['failure_rate']:.2f}%", STATUS_CRITICAL),
        )

        row = tk.Frame(parent, bg="#FAFBFC")
        row.pack(fill="x", padx=12, pady=(10, 4))
        for index, (label, value, color) in enumerate(tiles):
            row.grid_columnconfigure(index, weight=1, uniform="stat-tile")
            tile = tk.Frame(
                row, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1
            )
            tile.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 6, 0))
            tk.Label(
                tile, text=value, font=("맑은 고딕", 16, "bold"), fg=color, bg=self.CARD
            ).pack(pady=(12, 0))
            tk.Label(
                tile, text=label, font=("맑은 고딕", 9), fg=self.SUBTEXT, bg=self.CARD
            ).pack(pady=(0, 12))

    def _build_chart_grid(self, parent, chart_specs):
        """분석 그래프 카드들을 2열 그리드로 배치한다. chart_specs는 Visualizer.chart_specs()의 결과."""
        grid = tk.Frame(parent, bg="#FAFBFC")
        grid.pack(fill="both", expand=True, padx=12, pady=(6, 16))
        grid.grid_columnconfigure(0, weight=1, uniform="chart-col")
        grid.grid_columnconfigure(1, weight=1, uniform="chart-col")

        for index, (title, plot_fn, description, keyword) in enumerate(chart_specs):
            row, column = divmod(index, 2)
            card = self._create_chart_card(grid, title, description, keyword)
            card.grid(row=row, column=column, sticky="nsew", padx=6, pady=(0, 12))

            figure = Figure(figsize=(4.0, 2.9), dpi=100)
            axes = figure.add_subplot(1, 1, 1)
            plot_fn(figure, axes)
            figure.tight_layout()

            canvas = FigureCanvasTkAgg(figure, master=card)
            canvas.draw()
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.configure(bg=self.CARD, highlightthickness=0, cursor="hand2")
            canvas_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            canvas_widget.bind(
                "<Button-1>",
                lambda event, c=card, t=title, d=description, k=keyword: self._toggle_chart_tooltip(
                    event, c, t, d, k
                ),
            )

    def _create_chart_card(self, parent, title, description, keyword):
        """그래프 하나를 담을 카드(제목 + 본문 영역)를 만들어 반환한다.

        카드나 제목을 클릭하면 설명 툴팁이 뜨고, 동시에 오른쪽 뉴스 패널이 keyword로 다시
        검색된다 (그래프 인사이트 ↔ 관련 뉴스 연결).
        """
        card = tk.Frame(
            parent,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            cursor="hand2",
        )
        title_label = tk.Label(
            card,
            text=title,
            font=("맑은 고딕", 10, "bold"),
            fg=self.TEXT,
            bg=self.CARD,
            cursor="hand2",
        )
        title_label.pack(anchor="w", padx=12, pady=(10, 0))

        for widget in (card, title_label):
            widget.bind(
                "<Button-1>",
                lambda event, c=card, t=title, d=description, k=keyword: self._toggle_chart_tooltip(
                    event, c, t, d, k
                ),
            )
        return card

    def _toggle_chart_tooltip(self, event, source_widget, title, description, keyword):
        """같은 카드를 다시 클릭하면 닫고, 다른 카드를 클릭하면 그쪽 설명으로 바꿔 연다.

        새로 열 때(같은 카드를 닫기만 하는 게 아닐 때)만 오른쪽 뉴스 패널을 keyword로 다시 검색한다.
        """
        was_same_source = self._chart_tooltip_source is source_widget
        self._close_chart_tooltip()
        if not was_same_source:
            self._open_chart_tooltip(event, source_widget, title, description)
            self._search_news_for_chart(title, keyword)
        # 이 클릭이 "빈 곳 클릭"으로도 처리돼 방금 연 툴팁이 바로 닫히지 않도록 전파를 막는다.
        return "break"

    def _search_news_for_chart(self, chart_title, keyword):
        """그래프 카드의 인사이트(keyword)로 오른쪽 뉴스 패널을 다시 검색한다."""
        self._crawler.search_word = keyword
        self.news_subtitle_var.set(f"네이버 뉴스 검색  ·  {keyword}  ({chart_title} 관련)")
        self.refresh_news()

    def _open_chart_tooltip(self, event, source_widget, title, description):
        """클릭한 지점 근처에 제목+설명을 담은 작은 툴팁 박스(테두리 없는 Toplevel)를 띄운다."""
        tooltip = tk.Toplevel(self)
        tooltip.overrideredirect(True)
        tooltip.attributes("-topmost", True)
        tooltip.configure(bg=self.BORDER)

        inner = tk.Frame(tooltip, bg=self.CARD)
        inner.pack(padx=1, pady=1)
        tk.Label(
            inner,
            text=title,
            font=("맑은 고딕", 10, "bold"),
            fg=self.TEXT,
            bg=self.CARD,
            anchor="w",
            justify="left",
        ).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(
            inner,
            text=description,
            font=("맑은 고딕", 9),
            fg=self.SUBTEXT,
            bg=self.CARD,
            anchor="w",
            justify="left",
            wraplength=260,
        ).pack(anchor="w", padx=14, pady=(0, 12))

        # 화면 밖으로 나가지 않도록, 필요하면 클릭 지점의 반대쪽에 붙인다.
        tooltip.update_idletasks()
        tooltip_width = tooltip.winfo_width()
        tooltip_height = tooltip.winfo_height()
        x = event.x_root + 16
        y = event.y_root + 16
        if x + tooltip_width > tooltip.winfo_screenwidth():
            x = event.x_root - tooltip_width - 16
        if y + tooltip_height > tooltip.winfo_screenheight():
            y = event.y_root - tooltip_height - 16
        tooltip.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        self._chart_tooltip = tooltip
        self._chart_tooltip_source = source_widget

    def _close_chart_tooltip(self):
        """열려 있는 설명 툴팁이 있으면 닫는다."""
        if self._chart_tooltip is not None:
            self._chart_tooltip.destroy()
            self._chart_tooltip = None
            self._chart_tooltip_source = None

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
            news_items = self._crawler.fetch_news_items()
            self._schedule_on_ui_thread(self._show_news, news_items)
        except CRAWL_ERRORS as error:
            self._schedule_on_ui_thread(self._show_error, str(error))

    def _schedule_on_ui_thread(self, callback, *args):
        """백그라운드 스레드 결과를 메인 스레드에 안전하게 전달한다.

        크롤링이 끝나기 전에 사용자가 창을 닫으면 self.after() 호출 시점에 Tk 인터프리터가
        이미 종료돼 있어 RuntimeError가 난다. 창이 닫힌 뒤 뒤늦게 도착한 결과는 조용히 버린다.
        """
        try:
            self.after(0, callback, *args)
        except (RuntimeError, tk.TclError):
            pass

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