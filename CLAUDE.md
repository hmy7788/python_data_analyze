# CLAUDE.md

이 파일은 이 저장소에서 작업하는 Claude Code(claude.ai/code)에게 제공하는 가이드입니다.

## 프로젝트 개요

이 미니 프로젝트의 확정 주제는 **CNC 설비 정상/불량 판별**(`Machine failure` 컬럼 기준 이진 분류)이며,
이미 저장소에 있는 UCI AI4I 2020 Predictive Maintenance 데이터셋(`ai4i2020.csv`)을 사용합니다. 제조 데이터를
별도로 크롤링할 계획은 없으며, 앞으로도 `ai4i2020.csv`가 유일한 데이터 소스입니다.

1. **EDA 노트북** (`EDA.ipynb`, `EDA2.ipynb`) — `ai4i2020.csv` 분석. 완료되었으며 `README.md`에 정리되어 있음.
2. **`main.py`** (Tkinter UI) + **`visualizer.py`** (그래프) + **`crawler.py`** (크롤링)로 모듈이 나뉘어
   있습니다. 오른쪽 패널은 (이 주제와는 무관하게 기존에 있던) "CNC 불량" 네이버 뉴스 크롤러이며, 실제 수집
   로직은 `crawler.py`의 `DataCrawler`에 있습니다. 왼쪽 패널의 **"전체 데이터 한 눈에 보기" 화면은 구현
   완료**되어 `ai4i2020.csv`를 요약 카드 4개 + 그래프 12개로 렌더링합니다. "모델 훈련 결과 보기"와 "모델
   입력하기" → 예측 연동은 아직 자리표시자(placeholder) 상태입니다 (아래 절 참고).
3. **`미니 프로젝트 흐름도.png`** — 원래 구상했던 더 큰 파이프라인
   ("현대오토에버 제조데이터 미니 프로젝트 (분류/회귀)")의 흐름도 스펙: 크롤링 → 전처리 → 시각화(EDA) →
   리터러시(Q→A) → 모델링(분류/회귀) → 평가 → 저장 → 보고서, `crawler.py`/`preprocessor.py`/`visualizer.py`/
   `literacy.py`/`modeling.py`/`evaluation.py`/`report.py` 모듈 포함. **프로젝트 결정에 따라 전처리/모델링/평가/
   저장/보고서 단계(및 크롤링 단계)는 나중으로 미룹니다** — 현재 작업 범위는 EDA/전체 데이터 보기 패널로
   한정합니다. 아래 모듈/함수 이름은 나중에 해당 작업을 재개할 때 참고용으로 남겨둔 것이며, 미리 앞서서
   만들 필요는 없습니다.
4. **`docs/troubleshooting.md`** — 이 프로젝트의 진행형 트러블슈팅 기록입니다. **작업 중 실제 에러/이슈를
   겪고 해결했다면 행을 추가하세요**: 발생 단계 / 에러·이슈 내용 / 원인 / 해결 방법 / 예방 대책. 흐름도
   이미지의 "에러/이슈 정리" 표 형식을 그대로 따릅니다.

## 명령어

빌드 시스템, 린터, 테스트 스위트는 별도로 구성되어 있지 않습니다. 순수 스크립트/노트북 기반 프로젝트입니다.

```bash
# 환경 설정 (저장소에 venv/가 이미 있음; 필요 시 재생성)
pip install pandas numpy matplotlib seaborn jupyter

# 메인 EDA 노트북을 처음부터 끝까지 재실행 (README.md가 참조하는 images/*.png를 재생성함)
jupyter nbconvert --to notebook --execute --inplace EDA.ipynb

# Tkinter 앱 실행 (네이버 뉴스 크롤링을 위해 인터넷 연결 필요)
python main.py
```

## 아키텍처

### EDA 노트북
- `EDA.ipynb`는 `README.md`가 참조하는 메인 분석 노트북으로, `images/` 아래의 모든 차트를 생성합니다
  (히스토그램, 상관관계 히트맵, 고장 분포, 세부 고장 모드, 고장 여부별 박스플롯, Type별 고장률).
- `EDA2.ipynb`는 같은 데이터셋으로 컬럼 선택/그룹핑/정렬/시각화 연습에 초점을 맞춘 2차 노트북이며(노트북
  맨 앞 markdown 셀 참고), `EDA2.html`로 export되어 있습니다.
- `ai4i2020.csv`(10,000행 × 14열)는 결측치·중복행이 없지만, `Type`과 `Product ID`에 앞뒤 공백이 섞여 있어
  groupby/join 전에 반드시 strip해야 합니다 (`EDA2.ipynb` 초반의 `.str.strip()` 호출 참고).
- 이후 모델링 작업에 참고해야 할 분석 결과(`README.md` 기준):
  - 타겟 `Machine failure`의 클래스 불균형이 심함(양성 3.39%) — accuracy 대신 recall/precision/F1/ROC-AUC
    사용, 리샘플링(SMOTE)이나 `class_weight` 고려.
  - 강한 다중공선성: `Air temperature` ↔ `Process temperature` (+0.88), `Rotational speed` ↔ `Torque`
    (−0.88) — 선형모델/특성 선택 시 유의.
  - 5개 세부 고장 모드 플래그(`TWF`, `HDF`, `PWF`, `OSF`, `RNF`)가 `Machine failure`와 완전히 일치하지 않음
    (불일치 27건) — 원본 라벨링이 100% 결정론적이지 않으며, 특히 `RNF`가 그러함.
  - 고장 예측에 가장 유효한 변수: `Torque` > `Tool wear` > `Air temperature`; 제품 `Type` 등급이 높을수록
    고장률이 낮아짐 (L 3.92% > M 2.77% > H 2.09%).

### `main.py` — Tkinter 데스크톱 UI 셸 (UI 전용, 크롤링/그래프 내용은 모른다)
하나의 `Frame` 안에서 `grid`로 좌/우를 나눈 단일 파일 앱입니다. **`main.py`는 위젯 조립만 담당하고, "무엇을
그릴지"/"무엇을 어떻게 수집할지"는 전혀 알지 못합니다** — 그래프는 `visualizer.py`의 `Visualizer`, 크롤링은
`crawler.py`의 `DataCrawler`에 위임합니다.

- **오른쪽 패널 (동작함):** `crawler.SEARCH_WORD`("CNC 불량")에 대한 네이버 뉴스 대시보드. `__init__`에서
  만든 `self._crawler = DataCrawler()` 인스턴스를 재사용하며, `_load_news_worker()`가 Tk 메인루프를 막지
  않도록 백그라운드 `threading.Thread`에서 `self._crawler.fetch_news_items()`를 호출하고
  `crawler.CRAWL_ERRORS`로 실패를 잡습니다. 결과 콜백은 직접 `self.after(...)`를 부르지 않고
  `_schedule_on_ui_thread(callback, *args)`를 거칩니다 — 크롤링이 끝나기 전에 창이 닫히면 Tk 인터프리터가
  이미 종료돼 `self.after()`가 `RuntimeError`를 던지는데, 이 헬퍼가 그 경우를 조용히 무시합니다
  (`docs/troubleshooting.md` 참고). **백그라운드 스레드에서 Tk 위젯을 건드리는 새 코드를 추가할 때는 이
  헬퍼를 재사용하세요.** 기사 제목을 클릭하면 `crawler.open_in_chrome()`이 호출되며,
  `PROGRAMFILES`/`PROGRAMFILES(X86)`/`LOCALAPPDATA`에서 Chrome을 찾고 없으면 `webbrowser.open_new_tab`으로
  대체합니다. 검색어/개수를 바꾸고 싶으면 `main.py`를 고치지 말고 `DataCrawler(search_word=..., count=...)`
  생성 인자를 바꾸세요.
- **왼쪽 패널:** "전체 데이터 한 눈에 보기" / "모델 훈련 결과 보기" / "모델 입력하기" 3개의 nav 버튼이
  `_select_left_view()`를 통해 라우팅되며, 각각 `self.data_box`의 내용을 교체합니다.
  - `_show_all_data_view()` (**구현 완료**)는 `_load_dataset()`으로 `ai4i2020.csv`를 지연 로드하고
    (`self._dataset`에 캐시, `EDA2.ipynb`와 동일하게 컬럼명과 `Type`의 공백을 strip), 로드한 `DataFrame`으로
    `Visualizer(dataset)`을 만듭니다. 화면은 `_make_scrollable()`이 만든 세로 스크롤 영역(Canvas +
    Scrollbar, 마우스가 위에 있을 때만 휠 스크롤 바인딩) 안에 구성되며, 로드 실패 시 예외를 그대로 던지지
    않고 `_show_data_error()`로 표시합니다.
    - `_build_stat_tiles(parent, summary)` — `visualizer.summarize_status()`가 계산한 전체/정상/불량/
      불량률 dict를 받아 요약 카드 4개를 그립니다.
    - `_build_chart_grid(parent, chart_specs)` — `visualizer.chart_specs()`가 반환하는
      `(제목, plot_fn, 설명)` 목록을 순서대로 2열 그리드에 배치합니다. 각 카드는 `_create_chart_card()`로
      만들고, 카드마다 별도의 `matplotlib` `Figure`를 만들어 `plot_fn(figure, axes)`를 호출한 뒤
      `FigureCanvasTkAgg`로 붙입니다. **어떤 그래프를 보여줄지, 몇 개인지, 설명 문구는 무엇인지는 전부
      `visualizer.py` 쪽 책임** — 그래프를 추가/제거/수정하려면 `main.py`가 아니라
      `Visualizer.chart_specs()`를 고치면 됩니다.
    - **그래프 카드를 클릭하면 설명 툴팁이 뜬다.** 카드나 제목을 클릭하면 `_toggle_chart_tooltip()`이
      `_open_chart_tooltip()`으로 `overrideredirect(True)` `Toplevel`(테두리 없는 작은 박스, 팝업 창이
      아님)을 클릭 지점 근처에 띄우고 `chart_specs()`의 설명 문구를 보여줍니다. 같은 카드를 다시 클릭하면
      닫히고, 다른 카드를 클릭하면 그쪽 설명으로 바뀌며, 카드 밖(윈도우 배경)을 클릭하거나 그래프 영역을
      스크롤하거나 다른 nav 화면으로 전환하면(`_clear_data_box()`에서 처리) 자동으로 닫힙니다. 카드 쪽
      클릭 핸들러가 `"break"`를 반환해, `self.bind("<Button-1>", ...)`으로 걸어둔 "빈 곳 클릭 시 닫기"
      바인딩과 충돌하지 않도록 되어 있습니다 — 새로운 클릭형 위젯을 추가할 때 이 패턴을 참고하세요.
  - `_show_training_result_view()`는 아직 `[모델 훈련 결과 화면 연결 위치]` 주석이 달린 자리표시자입니다 —
    위 프로젝트 결정에 따라 모델링/평가와 함께 나중으로 미룹니다.
  - `MODEL_INPUT_NAMES = ("type", "air_temp", "proc_temp", "rot_speed", "torque", "tool_wear")`는 6개
    입력 `Entry`의 배치 순서이자 이후 모델에 전달될 변수명이므로, 학습된 모델이 기대하는 피처 순서와 반드시
    맞춰야 합니다.
  - `_save_model_inputs()`는 6개 입력값을 `self.model_input_values`에 담고 `self.<name>` 속성에도 동일한
    값을 반영한 뒤 `_on_model_input_saved()`를 호출합니다 — 실제 `model.predict(...)` 호출을 연결할 지점으로
    표시되어 있으며(`# Data 모델링 팀이 예측 함수 호출 코드를 연결할 위치다`), 현재는 값을 `print()`만 합니다.
    모델링 단계로 미룬 상태입니다.

### `visualizer.py` — 그래프 전용 모듈 (Tkinter를 모른다)
`ai4i2020.csv`를 `matplotlib`으로 그리는 로직만 담당하며, Tkinter는 import조차 하지 않습니다. 흐름도가
지정한 `visualizer.py` / `Visualizer` 이름과 `plot_dist()`/`plot_corr()`/`plot_box()`/`plot_scatter()`
메서드 이름을 그대로 따랐습니다 (아래 "목표 파이프라인 모듈" 표 참고 — 이 모듈은 예정보다 먼저 구현됨).

- `Visualizer(dataframe)`으로 생성. 내부 상태는 `self.dataframe` 하나뿐입니다.
- `summarize_status()` — 전체/정상/불량 건수와 불량률 dict. UI 요약 카드가 그대로 소비합니다.
- `chart_specs()` — `(제목, plot_fn, 설명)` 튜플 12개. **"전체 데이터 한 눈에 보기"에 어떤 차트를 몇 개, 무슨
  순서, 무슨 설명으로 보여줄지는 이 메서드가 결정**합니다. 설명은 UI가 그래프 카드를 클릭했을 때 툴팁으로
  보여주는 한글 문장이므로, 그래프를 추가/수정할 때 반드시 같이 채워야 합니다. 각 `plot_fn`은
  `plot_fn(figure, axes)` 시그니처로, 흐름도의 4개 범용 메서드를 구체적인 컬럼에 바인딩한 람다이거나 전용
  메서드입니다:
  - `plot_status_distribution`, `plot_type_distribution`, `plot_failure_rate_by_type`, `plot_corr`,
    `plot_failure_mode_counts` — 이 프로젝트 전용 차트. `plot_failure_mode_counts`는 세부 고장 모드
    (`TWF`/`HDF`/`PWF`/`OSF`/`RNF`, `FAILURE_MODE_COLUMNS`/`FAILURE_MODE_LABELS`)별 발생 건수를 보여줍니다
    — `README.md`의 EDA 5번 항목("세부 고장 모드")을 UI로 옮긴 것입니다.
  - `plot_dist(figure, axes, column, x_label)` — 정상/불량 상태별 분포를 겹쳐 그리는 히스토그램 (흐름도의
    `plot_dist`). `chart_specs()`에서 Torque, Tool wear, Rotational speed, Air temperature 총 4번
    재사용됩니다.
  - `plot_scatter(figure, axes, x_column, y_column, x_label, y_label)` — 정상/불량 색으로 나눈 산점도
    (흐름도의 `plot_scatter`). 회전속도-토크, 기온-공정온도(다중공선성 +0.88 확인용) 2번 사용됩니다.
  - `plot_box(figure, axes, column, y_label)` — 정상/불량 박스플롯 (흐름도의 `plot_box`).
- 색상 상수(`STATUS_GOOD`, `STATUS_CRITICAL`, `SEQUENTIAL_BLUE`, `DIVERGING_CMAP`), 상관관계 컬럼/라벨
  목록(`CORRELATION_COLUMNS`, `CORRELATION_LABELS`), 세부 고장 모드 컬럼/라벨 목록
  (`FAILURE_MODE_COLUMNS`, `FAILURE_MODE_LABELS`)이 모듈 최상단에 있습니다. **정상/불량 두 상태를 나타내는
  모든 그래프는 `STATUS_GOOD`(초록)/`STATUS_CRITICAL`(빨강)을 일관되게 재사용합니다** — 새 그래프를 추가할
  때도 이 색상 조합을 그대로 따르세요.
- 한글 차트 라벨은 모듈 임포트 시점에 설정하는 `matplotlib.rcParams["font.family"] = "Malgun Gothic"`에
  의존하므로, 이 설정을 지우면 한글 라벨이 깨진 네모(tofu box)로 표시됩니다.
- `main.py`가 아닌 다른 곳(예: 나중의 `report.py`)에서도 그대로 재사용할 수 있도록, `Visualizer`는 Tkinter나
  파일 경로에 의존하지 않고 순수하게 `DataFrame` → `matplotlib` `Figure`/`Axes`만 다룹니다.

### `crawler.py` — 크롤링 전용 모듈 (Tkinter를 모른다)
네이버 뉴스 검색 결과를 가져오는 로직만 담당하며, Tkinter는 import조차 하지 않습니다. 흐름도가 지정한
`crawler.py` / `DataCrawler` 이름과 `collect()`/`parse()` 메서드 이름을 따랐습니다 (아래 "목표 파이프라인
모듈" 표 참고 — `save_raw()`는 아직 미구현: 지금은 UI가 매번 새로 불러올 뿐 수집 결과를 파일로 남기지
않습니다).

- `DataCrawler(search_word=SEARCH_WORD, count=NEWS_COUNT)`로 생성. 내부 상태는 `search_word`/`count`
  두 개뿐입니다.
- `collect()` — 네이버 뉴스 검색 결과 페이지를 요청해 HTML 원문(str)을 반환합니다 (흐름도의 `collect`).
- `parse(page_html)` — `NaverNewsParser`(`HTMLParser` 서브클래스, 기존 `news_tit` 앵커 마크업과 신규
  `text-type-headline` 마크업을 모두 처리)로 HTML에서 `{"title": ..., "url": ...}` 목록을 뽑아 `count`개까지
  자릅니다 (흐름도의 `parse`). 결과가 비어 있으면 `RuntimeError`를 던집니다.
- `fetch_news_items()` — `collect()` + `parse()`를 순서대로 실행하는 편의 메서드. `main.py`는 이것만
  호출합니다.
- `CRAWL_ERRORS` — `main.py`가 크롤링 실패를 잡을 때 쓰는 예외 튜플(`HTTPError`, `URLError`,
  `TimeoutError`, `RuntimeError`, `OSError`).
- `open_in_chrome(url)` — 모듈 최상단 함수(클래스 밖). 크롤링 결과 URL을 여는 동작이라 이 모듈에 뒀습니다.
- `main.py`가 아닌 다른 곳에서도 재사용할 수 있도록, `DataCrawler`는 Tkinter나 UI 상태에 의존하지 않고
  순수하게 "검색어 → HTML → 기사 목록"만 다룹니다.

### 목표 파이프라인 모듈 (`미니 프로젝트 흐름도.png` 기준)
나중에 파이프라인의 나머지를 만들 때는, 새 이름을 만들지 말고 흐름도가 지정한 아래 모듈/클래스/함수
구성을 따라야 `main.py`의 UI 연결 지점들과 자연스럽게 이어집니다:

| 파일 | 클래스 | 메서드 | 상태 |
| --- | --- | --- | --- |
| `crawler.py` | `DataCrawler` | `collect()`, `parse()`, `save_raw()` | `collect()`/`parse()` **구현 완료** (위 절 참고), `save_raw()`는 미구현·보류 |
| `preprocessor.py` | `Preprocessor` | `load()`, `clean_missing()`, `encode()`, `scale()`, `feature_engineering()`, `save_processed()` | 미구현, 보류 |
| `visualizer.py` | `Visualizer` | `plot_dist()`, `plot_corr()`, `plot_box()`, `plot_scatter()` | **구현 완료** (위 절 참고) |
| `literacy.py` | `Literacy` | `ask_question()`, `analyze()`, `answer_qa()` | 미구현, 보류 |
| `modeling.py` | `Modeler` | `train()`, `predict()`, `save_model()` | 미구현, 보류 |
| `evaluation.py` | `Evaluator` | `classification_metrics()`, `regression_metrics()`, `plot_confusion()` | 미구현, 보류 |
| `report.py` | (모듈 함수) | `make_report()`, `save_html()`, `save_pdf()` | 미구현, 보류 |

흐름도가 명시한 산출물: `processed.csv`(전처리된 데이터), `model.joblib`(학습된 모델), `report.html` /
`report.pdf`(자동 생성 보고서), `run.log`(실행 로그). 흐름도는 또한 기본적인 입력/전처리/모델 검증도
요구합니다(입력 단계: CSV 형식 및 필수 컬럼 검증; 전처리 후: 결측치/이상치/인코딩 확인; 학습 후: 교차검증
점수 및 train/test 과적합 확인). 크롤링/전처리/모델링/저장 단계별 예상 에러 케이스와 대응 방법을 정리한
표도 있으니, 파이프라인 코드를 새로 추가하기 전에 확인해 볼 가치가 있습니다 — 이 프로젝트가 맞춰야 할
에러 처리 수준을 정의하고 있기 때문입니다.
