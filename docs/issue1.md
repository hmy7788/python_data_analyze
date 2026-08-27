# 에러 제목

그래프 카드를 빠르게 연달아 클릭하면 최신 검색어와 다른(엉뚱한) 뉴스가 화면에 남는 문제

1. "세부 고장 모드별 발생 건수" 카드 클릭 → 오른쪽 부제목이 `CNC 방열 고장`으로 바뀌며 검색 시작
2. 결과가 뜨기 전에 곧바로 "회전속도 vs 토크" 카드 클릭 → 부제목이 `CNC 회전속도 저하 원인`으로 바뀜
3. 잠시 후 화면 — 부제목은 `CNC 회전속도 저하 원인`인데, 실제 기사 목록은 `CNC 방열 고장` 검색 결과가 표시됨

# 문제 원인 분석

- **발생 위치**: `src/UI/main.py`, `refresh_news()` / `_load_news_worker()` / `_show_news()`
- **발생 조건**: 그래프 카드 A를 클릭한 뒤, A의 뉴스 검색이 끝나기 전에 카드 B를 연달아 클릭할 때 (짧은 시간 안에 카드를 2번 이상 클릭)
- **에러 메시지**: 에러가 나서 죽는 건 아니고, 화면에 "검색어(부제목)"와 "실제 기사 목록"이 서로 어긋나는 논리적 버그였음
- **추정 원인**: 카드를 클릭할 때마다 `refresh_news()`가 매번 새로운 백그라운드 스레드(`threading.Thread`)를 띄워 네이버에 검색을 요청함. 그런데 "이 결과가 최신 클릭에 대한 것인지" 확인하는 장치가 없어서, 먼저 시작했지만 네트워크가 느려 늦게 끝난 A의 결과가, 이미 화면에 표시된 더 최신 요청(B)의 결과를 뒤늦게 덮어써 버림. 비유하자면 "먼저 주문한 음식이 늦게 나와서, 이미 받은 나중 주문 위에 잘못 올라온" 상황

# 문제 해결 방법

클릭할 때마다 검색 요청에 번호(순번)를 매기고, 결과가 도착했을 때 "그 번호가 지금 가장 최신 요청과 같은 경우"에만 화면을 갱신하도록 가드를 추가함.

# 수정한 코드

```python
# 기존 (문제 발생) — 결과가 도착하면 무조건 화면을 갱신
def refresh_news(self):
    threading.Thread(target=self._load_news_worker, daemon=True).start()

def _load_news_worker(self):
    news_items = self._crawler.fetch_news_items()
    self.after(0, self._show_news, news_items)  # 늦게 도착한 결과도 그대로 반영됨

# 수정 — 요청마다 번호를 매기고, 최신 요청일 때만 반영
def refresh_news(self):
    self._news_request_id += 1
    threading.Thread(
        target=self._load_news_worker, args=(self._news_request_id,), daemon=True
    ).start()

def _load_news_worker(self, request_id):
    news_items = self._crawler.fetch_news_items()
    self._schedule_on_ui_thread(self._apply_if_current, request_id, self._show_news, news_items)

def _apply_if_current(self, request_id, callback, arg):
    # 더 최신 요청이 이미 시작된 뒤에 도착한 오래된 결과는 조용히 버림
    if request_id == self._news_request_id:
        callback(arg)
```

# 문제 해결 결과

그래프 카드를 여러 번 빠르게 연달아 클릭해도, 화면에는 항상 가장 마지막으로 클릭한 카드의 검색어와 그 결과만 표시됨. 먼저 시작했지만 늦게 끝난 이전 요청의 결과는 화면에 반영되지 않고 무시됨.

# 결과

- 사용자가 짧은 시간에 여러 번 트리거할 수 있는 백그라운드 작업(크롤링, 향후 모델 예측 등)을 새로 추가할 때는, 항상 "이 결과가 아직 최신 요청에 대한 것인가?"를 확인하는 요청 ID 가드를 함께 넣기로 함
- 이 패턴(`_news_request_id` + `_apply_if_current`)을 `docs/troubleshooting.md`와 `CLAUDE.md`에 기록해, 나중에 비슷한 기능(예: 모델 예측 버튼 연타)을 추가할 때 그대로 재사용하기로 함
