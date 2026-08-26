# 트러블슈팅 기록

CNC 설비 정상/불량 판별 미니 프로젝트를 진행하며 겪은 에러/이슈를 단계별로 기록한다.
새 이슈가 생기면 아래 표에 행을 추가한다. (참고: `미니 프로젝트 흐름도.png`의 "에러/이슈 정리" 표 형식)

| 발생 단계 | 에러/이슈 내용 | 원인 | 해결 방법 | 예방 대책 |
| --- | --- | --- | --- | --- |
| UI (main.py, 크롤링) | 크롤링이 끝나기 전에 창을 닫으면 백그라운드 스레드에서 `RuntimeError: main thread is not in main loop`가 발생 (`self.after()` 호출부, `main.py`) | `_load_news_worker()`가 백그라운드 `threading.Thread`에서 `self._crawler.fetch_news_items()`가 끝난 뒤 `self.after(0, ...)`로 결과를 메인 스레드에 넘기는데, 그 사이 사용자가 창을 닫아 `self.destroy()`가 먼저 실행되면 Tk 인터프리터가 이미 종료된 상태라 `self.after()` 호출이 실패함 | `_schedule_on_ui_thread(callback, *args)` 헬퍼를 추가해 `self.after()` 호출을 `try/except (RuntimeError, tk.TclError)`로 감쌈 — 창이 닫힌 뒤 뒤늦게 도착한 콜백은 조용히 버림. `_load_news_worker()`가 이 헬퍼를 거쳐 `_show_news`/`_show_error`를 예약하도록 변경 | 백그라운드 스레드에서 Tk 위젯을 건드리거나 `self.after()`를 호출하는 코드는 항상 `_schedule_on_ui_thread()`처럼 방어적으로 감쌀 것. 새 백그라운드 작업을 추가할 때 이 패턴을 재사용 |

## 작성 가이드

- **발생 단계**: 크롤링 / 전처리 / 시각화(EDA) / 모델링 / 평가 / 저장 / 보고서 / UI(main.py) 중 해당하는 단계.
- **에러/이슈 내용**: 실제 에러 메시지 또는 증상을 그대로 옮겨 적는다.
- **원인**: 로그·트레이스백을 보고 확인한 근본 원인.
- **해결 방법**: 실제로 적용한 조치 (코드 변경, 설정 변경 등).
- **예방 대책**: 같은 문제가 재발하지 않도록 앞으로 지킬 규칙.
