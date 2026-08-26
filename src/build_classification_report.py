"""classifications.ipynb 결과를 정적 HTML 리포트로 만드는 스크립트.

노트북을 다시 학습시키지 않고, 이미 노트북을 실행해서 확인한 지표(README.md/CLAUDE.md에도
정리된 값)를 그대로 표로 옮기고 저장된 그래프(images/model_*.png)를 끼워 넣는다. 여기에 더해,
main.py가 EDA 차트 카드에서 하던 것과 같은 방식으로 "이 분석 결과의 인사이트로 뉴스를 검색"해서
리포트 하단에 관련 기사를 붙인다 — 크롤링을 이 리포트에 적용하는 방법은 그래프 인사이트 기반
검색이라는 기존 설계를 그대로 재사용하는 것이다.

실행: 저장소 루트에서 `python src/build_classification_report.py`
출력: 저장소 루트의 `classification_report.html`
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawler import CRAWL_ERRORS, DataCrawler  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "classification_report.html"

# classifications.ipynb를 실행해서 확인한 값 (파생변수 4개 포함, 모델 4개, random_state=42 고정)
METRICS = [
    {"모델": "XGBoost", "정확도": 0.494, "정밀도": 0.327, "재현율": 0.332, "F1": 0.328, "AUC": 0.503},
    {"모델": "Random Forest", "정확도": 0.492, "정밀도": 0.326, "재현율": 0.330, "F1": 0.325, "AUC": 0.509},
    {"모델": "Logistic Regression", "정확도": 0.239, "정밀도": 0.329, "재현율": 0.330, "F1": 0.233, "AUC": 0.497},
    {"모델": "SVM", "정확도": 0.223, "정밀도": 0.304, "재현율": 0.297, "F1": 0.218, "AUC": 0.478},
]

# 이 리포트의 핵심 발견(AUC가 전 모델 0.5 근처 = 랜덤 수준)을 검색어로 바꿔 관련 기사를 찾는다.
# main.py가 EDA 차트 카드마다 하는 "인사이트 -> 검색어" 매핑과 같은 방식이다.
SEARCH_KEYWORD = "제조업 AI 품질검사 한계"
NEWS_COUNT = 5


def fetch_related_news():
    crawler = DataCrawler(search_word=SEARCH_KEYWORD, count=NEWS_COUNT)
    try:
        return crawler.fetch_news_items(), None
    except CRAWL_ERRORS as error:
        return [], str(error)


def render_metrics_rows():
    rows = []
    for row in METRICS:
        rows.append(
            "<tr>"
            f"<td>{row['모델']}</td>"
            f"<td>{row['정확도']:.3f}</td>"
            f"<td>{row['정밀도']:.3f}</td>"
            f"<td>{row['재현율']:.3f}</td>"
            f"<td>{row['F1']:.3f}</td>"
            f"<td>{row['AUC']:.3f}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_news_items(news_items, error):
    if error:
        return f'<p class="muted">뉴스를 불러오지 못했습니다 ({error}).</p>'
    if not news_items:
        return '<p class="muted">관련 기사를 찾지 못했습니다.</p>'
    items = "\n".join(
        f'<li><a href="{item["url"]}" target="_blank" rel="noopener">{item["title"]}</a></li>'
        for item in news_items
    )
    return f"<ul>\n{items}\n</ul>"


def build_html():
    news_items, error = fetch_related_news()

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Type 분류 모델 비교</title>
<style>
  body {{
    max-width: 760px;
    margin: 3rem auto;
    padding: 0 1.5rem;
    font-family: -apple-system, "Malgun Gothic", "Segoe UI", sans-serif;
    line-height: 1.6;
    color: #222;
  }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.3rem; }}
  h2 {{ font-size: 1.1rem; margin-top: 2.5rem; border-bottom: 1px solid #ddd; padding-bottom: 0.4rem; }}
  p.subtitle {{ color: #666; margin-top: 0; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
  th, td {{ text-align: right; padding: 0.45rem 0.6rem; border-bottom: 1px solid #eee; }}
  th:first-child, td:first-child {{ text-align: left; }}
  th {{ color: #555; font-weight: 600; }}
  img {{ max-width: 100%; border: 1px solid #eee; border-radius: 4px; }}
  ul {{ padding-left: 1.2rem; }}
  li {{ margin-bottom: 0.3rem; }}
  a {{ color: #2a78d6; }}
  .muted {{ color: #888; font-size: 0.9rem; }}
  .finding {{ background: #f7f8fa; border-left: 3px solid #2a78d6; padding: 0.8rem 1rem; }}
</style>
</head>
<body>

<h1>Type(품질 등급) 분류 모델 비교</h1>
<p class="subtitle">ai4i2020.csv — Random Forest / XGBoost / Logistic Regression / SVM</p>

<h2>모델별 평가지표</h2>
<table>
<thead>
<tr><th>모델</th><th>정확도</th><th>정밀도</th><th>재현율</th><th>F1-score</th><th>AUC</th></tr>
</thead>
<tbody>
{render_metrics_rows()}
</tbody>
</table>

<h2>ROC Curve</h2>
<img src="images/model_roc_curves.png" alt="모델별 ROC Curve">

<h2>F1-score 비교</h2>
<img src="images/model_f1_comparison.png" alt="모델별 F1-score 비교">

<h2>결론</h2>
<p class="finding">
Temp_diff/Power/Torque_x_ToolWear/Failure_mode_count 같은 파생변수를 추가해도 AUC는 여전히 전 모델
0.48~0.51로 랜덤 수준이다. 센서값·고장 정보만으로는 <code>Type</code>(품질 등급)을 유의미하게
예측하지 못한다 — Type은 가동 중 측정값과 직접적 인과관계가 없는 식별자성 라벨에 가깝다는 뜻으로
해석된다.
</p>

<h2>관련 기사 ("{SEARCH_KEYWORD}")</h2>
{render_news_items(news_items, error)}

</body>
</html>
"""


if __name__ == "__main__":
    OUTPUT_PATH.write_text(build_html(), encoding="utf-8")
    print(f"written: {OUTPUT_PATH}")
