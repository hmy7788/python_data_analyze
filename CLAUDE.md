# CLAUDE.md

이 파일은 이 저장소에서 작업하는 Claude Code(claude.ai/code)에게 제공하는 가이드입니다.

## 프로젝트 개요

이 미니 프로젝트의 확정 주제는 **CNC 설비 정상/불량 판별**(`Machine failure` 컬럼 기준 이진 분류)이며,
이미 저장소에 있는 UCI AI4I 2020 Predictive Maintenance 데이터셋(`ai4i2020.csv`)을 사용합니다. 제조 데이터를
별도로 크롤링할 계획은 없으며, 앞으로도 `ai4i2020.csv`가 유일한 데이터 소스입니다.

**모든 `.py`/`.ipynb`/`.csv` 파일은 `src/` 아래에 있습니다** (`src/UI/main.py`, `src/UI/crawler.py`,
`src/UI/visualizer.py`, `src/UI/model_predictor.py`, `src/EDA1.ipynb`, `src/EDA2.ipynb`,
`src/model_1.ipynb`, `src/model_2.ipynb`, `src/model_3.ipynb`, `src/ai4i2020.csv`). 아래
본문에서 파일명만 적었으면 전부 `src/` 아래(단, Tkinter UI와 얽힌 4종은 `src/UI/` 아래)에 있다는
뜻입니다. Tkinter UI 4종(`main.py`/`crawler.py`/`visualizer.py`/`model_predictor.py`)만 서로 묶여서
`src/UI/`에 있고, 나머지 노트북/CSV는 그대로 `src/` 바로 아래에 있습니다 — `main.py`가
`from crawler import ...`/`from visualizer import ...`/`from model_predictor import ...`처럼 같은
폴더 기준 바로 임포트하기 때문에 항상 같이 옮겨야 합니다. `main.py`의 `DATA_PATH`는 `src/UI/`에서
한 단계 위 `src/ai4i2020.csv`를 가리키도록 `Path(__file__).resolve().parent.parent`를 쓰고,
`model_predictor.py`의 `MODEL_PATH`는 `src/UI/`에서 두 단계 위(저장소 루트) `model/`을 가리키도록
`Path(__file__).resolve().parent.parent.parent`를 씁니다.
`README.md`/`CLAUDE.md`/`docs/`/`images/`/`model/`/`미니 프로젝트 흐름도.png`는 저장소 루트에 그대로
남아 있습니다 — `images/`/`model/`이 `src/` 밖에 있기 때문에 `EDA1.ipynb`/`model_3.ipynb` 등의
`savefig()`/`joblib.dump()` 호출은 `"../images/*.png"`/`"../model/*.joblib"`처럼 한 단계 위로
올라가는 상대경로를 씁니다. 앞으로 `preprocessor.py` 등 새 모듈을 추가할 때도 `src/` 안에
만드세요(단, Tkinter UI와 얽힌 모듈이면 `src/UI/` 안에). 예외적으로 `scripts/run_notebook.py`만
저장소 루트의 `scripts/` 아래에 있습니다 — 노트북 실행용 도구라 `src/` 안 코드와는 성격이 달라
분리했습니다 (아래 "가상환경(`.venv/`)과 노트북 실행" 절 참고).

> **파일 이름 변경/삭제 이력** (착각하기 쉬운 부분): 원래 메인 EDA 노트북은 `EDA.ipynb`였지만 지금은
> `src/EDA1.ipynb`로 이름이 바뀌었습니다. `Type`(품질 등급) 다중분류를 다루던 `classifications.ipynb`와
> `Torque` 회귀를 다루던 `regression.ipynb`는 프로젝트 주제가 `Machine failure` 이진분류로 확정된 뒤
> **저장소에서 삭제**됐습니다 — 두 실험의 결과(표/그래프)는 `README.md` 2장(모델링 — 세 가지 예측 문제
> 비교)에 기록으로 남아 있고, 관련 이미지(`images/model_f1_comparison.png`, `images/model_roc_curves.png`,
> `images/regression_scatter.png`)도 그대로 있습니다. `src/EDA2.html`(EDA2.ipynb export본)도 같은
> 시점에 삭제됐습니다. 앞으로 이 파일들의 경로를 코드에서 참조하지 마세요 — 존재하지 않습니다.

1. **EDA 노트북** (`EDA1.ipynb`, `EDA2.ipynb`) — `ai4i2020.csv` 분석. 완료되었으며 `README.md`에 정리되어 있음.
2. **탐색 단계 모델링** — 확정 주제(`Machine failure` 이진분류)로 좁혀지기 전, `Type`(품질 등급) 다중분류
   4종 모델 비교(`classifications.ipynb`)와 `Torque` 회귀 4종 모델 비교(`regression.ipynb`)도 진행했습니다.
   두 노트북 모두 **결과까지 낸 뒤 저장소에서 삭제**됐고(위 "파일 이름 변경/삭제 이력" 참고), 결과는
   `README.md` 2장에 정리돼 있습니다 — `Type`은 사실상 랜덤 수준(AUC 0.48~0.51)이었고 `Torque`는 잘
   예측됨(R² 0.8+)을 확인한 것이 `Machine failure`로 주제를 확정하는 근거가 됐습니다. `미니 프로젝트
   흐름도.png`가 정의한 `modeling.py`/`Modeler` 모듈(아래 "목표 파이프라인 모듈" 표)과는 별개입니다.
3. **`src/model_1.ipynb`/`src/model_2.ipynb`** — `Machine failure` 이진분류의 초기 draft 노트북 2개
   (markdown 설명 없이 코드만 있음). `model_1.ipynb`는 SMOTE + RandomForest/XGBoost/LightGBM 단순 비교,
   `model_2.ipynb`는 피처 엔지니어링 + `RandomizedSearchCV`(recall 기준) 튜닝을 시도했습니다. 최종적으로
   위험구간(zone) 피처 엔지니어링을 적용한 **`model_3.ipynb`가 이 실험들을 이어받아 완성한 버전**이자
   실제 UI에 배포된 모델입니다 — 아래 `src/model_3.ipynb` 절 참고. `model_1`/`model_2`는 현재 UI와
   연결되어 있지 않고, 과거 실험 기록으로만 남아 있습니다.
4. **`main.py`** (Tkinter UI) + **`visualizer.py`** (그래프) + **`crawler.py`** (크롤링)로 모듈이 나뉘어
   있습니다. 오른쪽 패널은 네이버 뉴스 크롤러이지만, **더 이상 무관한 고정 검색어가 아니라 왼쪽 그래프
   카드가 알려주는 EDA 인사이트로 검색어가 바뀝니다** — 예: "세부 고장 모드별 발생 건수" 카드를 클릭하면
   `"CNC 방열 고장"`(실제 데이터에서 가장 흔한 고장 모드)으로 재검색됩니다. "크롤링이 우리 EDA 결과를
   실제 업계 뉴스로 뒷받침/검증해 보는" 용도로 자리를 잡았다는 점이 중요합니다 — 자세한 설계는 아래
   `main.py`/`visualizer.py` 절 참고. 실제 수집 로직은 `crawler.py`의 `DataCrawler`에 있습니다. 왼쪽
   패널의 **"전체 데이터 한 눈에 보기" 화면은 구현 완료**되어 `ai4i2020.csv`를 요약 카드 4개 + 그래프
   12개로 렌더링합니다. **"모델 훈련 결과 보기"와 "모델 입력하기" → 예측 연동도 구현 완료**됐습니다 —
   `src/model_3.ipynb`가 학습한 Random Forest(Enhanced 피처셋) 모델을 `model/random_forest_enhanced.joblib`
   로 저장해 두고, `src/UI/model_predictor.py`가 이를 불러와 두 화면에 각각 연결합니다 (아래 절 참고).
5. **`미니 프로젝트 흐름도.png`** — 원래 구상했던 더 큰 파이프라인
   ("현대오토에버 제조데이터 미니 프로젝트 (분류/회귀)")의 흐름도 스펙: 크롤링 → 전처리 → 시각화(EDA) →
   리터러시(Q→A) → 모델링(분류/회귀) → 평가 → 저장 → 보고서, `crawler.py`/`preprocessor.py`/`visualizer.py`/
   `literacy.py`/`modeling.py`/`evaluation.py`/`report.py` 모듈 포함. **프로젝트 결정에 따라 전처리/평가/
   저장/보고서 단계(및 크롤링 단계)는 나중으로 미룹니다** — `model_1.ipynb`~`model_3.ipynb`로 모델링
   (이진분류) 비교는 이미 진행했지만, 이는 흐름도가 정의한 `modeling.py`/`Modeler` 모듈 자체를 구현한
   것은 아닙니다. 아래 모듈/함수 이름은 나중에 `modeling.py` 등을 재개할 때 참고용으로 남겨둔 것이며,
   미리 앞서서 만들 필요는 없습니다.
6. **`docs/troubleshooting.md`** — 이 프로젝트의 진행형 트러블슈팅 기록입니다. **작업 중 실제 에러/이슈를
   겪고 해결했다면 행을 추가하세요**: 발생 단계 / 에러·이슈 내용 / 원인 / 해결 방법 / 예방 대책. 흐름도
   이미지의 "에러/이슈 정리" 표 형식을 그대로 따릅니다.

## 명령어

빌드 시스템, 린터, 테스트 스위트는 별도로 구성되어 있지 않습니다. 순수 스크립트/노트북 기반 프로젝트입니다.

```bash
# 환경 설정 (저장소에 .venv/가 이미 있음; 필요 시 재생성)
# 주의: `pip`가 PATH상 Anaconda 것을 먼저 찾아 .venv가 아닌 곳에 설치될 수 있으니
# (docs/troubleshooting.md 참고) 반드시 .venv의 python -m pip로 설치할 것
./.venv/Scripts/python -m pip install -r requirements.txt
# requirements.txt가 낡았거나 없다면 .venv 기준으로 새로 생성: ./.venv/Scripts/python -m pip freeze > requirements.txt
# (반드시 .venv의 pip로 생성할 것 — Anaconda 등 다른 인터프리터에서 freeze하면 이 프로젝트와 무관한
# 패키지 수백 개가 섞여 들어간다. requirements.txt에는 pandas/numpy/matplotlib/seaborn/jupyter/
# scikit-learn/xgboost/lightgbm/imbalanced-learn/joblib/nbclient/ipykernel이 포함되어 있어야 한다.)

# .venv 전용 Jupyter 커널 등록 (최초 1회만; 아래 노트북 재실행에 필요)
./.venv/Scripts/python -m ipykernel install --user --name cnc-venv --display-name "Python (.venv - CNC project)"

# 메인 EDA 노트북을 처음부터 끝까지 재실행 (저장소 루트의 images/eda_*.png를 재생성함)
# 주의: `jupyter nbconvert --execute`를 직접 쓰지 말 것 — 이 PC의 conda 자동 초기화 때문에
# 엉뚱한 인터프리터(Anaconda 베이스 등)로 조용히 새는 문제가 있다(docs/troubleshooting.md 참고).
# scripts/run_notebook.py가 nbclient로 커널을 못박아 이 문제를 우회한다. 이 스크립트는 nbconvert처럼
# 노트북이 있는 폴더(src/)를 작업 디렉터리로 실행하므로 상대경로(../images/*.png 등)는 그대로 동작한다.
./.venv/Scripts/python scripts/run_notebook.py src/EDA1.ipynb

# Machine failure(정상/불량) 이진분류 노트북 재실행 (images/modeling2_*.png와
# model/random_forest_enhanced.joblib을 재생성함 — UI가 이 joblib 파일을 그대로 불러 씀)
./.venv/Scripts/python scripts/run_notebook.py src/model_3.ipynb

# Tkinter 앱 실행 (저장소 루트에서 실행. 네이버 뉴스 크롤링을 위해 인터넷 연결 필요.
# "모델 훈련 결과 보기"/"모델 입력하기" 탭을 쓰려면 위 model_3.ipynb를 먼저 한 번 실행해
# model/random_forest_enhanced.joblib이 있어야 함)
./.venv/Scripts/python src/UI/main.py
```

### 가상환경(`.venv/`)과 노트북 실행 — 반드시 읽을 것
이 저장소는 원래 `venv/`를 썼지만 **`.venv/`로 교체**했습니다(`.gitignore`에도 `.venv/`가 등록돼
있음). `venv/`가 남아 있다면 그건 옛 흔적이니 참조하지 마세요.

이 PC(및 비슷하게 `conda init`이 셸 프로필에 등록된 PC)에서는 **새 PowerShell을 열 때마다
`VIRTUAL_ENV`/`CONDA_PREFIX`가 자동으로 주입**되는데, 이게 Jupyter의 커널 탐색 순서에 끼어들어서
`jupyter nbconvert --execute`가 **의도한 `.venv`가 아니라 엉뚱한 인터프리터(옛 `venv/`나 Anaconda
베이스)로 조용히 새는 문제**가 있습니다(에러 없이 "성공"하기 때문에 알아채기 어려움). 게다가
`--ExecutePreprocessor.kernel_name=...` CLI 플래그로 강제해도 이 환경에서는 무시됩니다(원인 미상,
PowerShell/Bash 양쪽에서 재현 확인). 자세한 원인 분석은 `docs/troubleshooting.md`의 "환경 설정
(`venv/`→`.venv/` 재구축, 노트북 실행)" 행 참고.

**그래서 노트북을 재실행할 때는 `jupyter nbconvert --execute`를 직접 쓰지 말고, 위 명령어 예시처럼
`scripts/run_notebook.py`를 쓰세요** — `nbclient`를 직접 호출해서 커널 이름(`cnc-venv`)을 코드로
못박기 때문에 PATH/VIRTUAL_ENV/CONDA_PREFIX가 무엇이든 항상 `.venv`가 실행됩니다. `cnc-venv`
커널이 아직 없다면 위 명령어의 `ipykernel install` 줄을 먼저 한 번 실행하세요. 실제로 어떤
인터프리터가 실행됐는지 확인하고 싶으면 출력의 경고문에 찍히는 파일 경로가 `.venv\Lib\site-packages\...`
인지 보면 됩니다.

`requirements.txt`를 다시 만들 때도 마찬가지로 `pip freeze`를 bare로 쓰지 말고 반드시
`./.venv/Scripts/python -m pip freeze`처럼 인터프리터를 직접 지정하세요 — bare `pip`/`python`은
PATH 맨 앞이 가리키는 곳(Anaconda 등)으로 샐 수 있습니다.

## 아키텍처

### EDA 노트북 (`src/EDA1.ipynb`, `src/EDA2.ipynb`, `src/ai4i2020.csv`)
- `src/EDA1.ipynb`(원래 이름은 `EDA.ipynb`였다가 리네임됨)는 `README.md`가 참조하는 메인 분석
  노트북으로, 저장소 루트의 `images/` 아래에 모든 차트를 생성합니다 (히스토그램, Type 분포, 고장 분포,
  세부 고장 모드, 상관관계 히트맵, 고장 여부별 박스플롯, Type별 고장률). 노트북이 `src/`에 있고
  `images/`는 루트에 있으므로 `savefig()` 호출은 `"../images/eda_*.png"` 형태의 상대경로를 씁니다 —
  `images/` 폴더를 옮기거나 노트북을 다른 곳으로 옮기면 이 상대경로도 같이 고쳐야 합니다.
  - **주의(실제로 겪은 버그)**: 첫 셀이 컬럼 *이름*은 strip하면서 `Type` *값*은 strip하지 않아서
    (원본 값이 `' L   '`처럼 앞뒤 공백 포함), `Type` 기준 `countplot`/`groupby` 차트 2개
    (`eda_type_dist.png`, `eda_failrate_by_type.png`)가 빈 그래프로 저장돼 있었다. `df["Type"] =
    df["Type"].str.strip()`를 첫 셀에 추가해 고쳤다. 추가로 `eda_failrate_by_type.png`는 pandas
    `Series.plot(kind="bar")`의 기본 90도 x축 라벨 회전이 Malgun Gothic 폰트와 결합하면 L/M/H가 깨진
    글자(ㄴ/∑/ㅍ처럼)로 렌더링되는 버그가 있어 `rot=0`으로 회전을 꺼서 우회했다. 앞으로 `Type`을 x축
    라벨로 쓰는 새 차트를 추가할 때 이 두 가지(strip 여부, rot=0)를 같이 확인할 것.
- `src/EDA2.ipynb`는 같은 데이터셋으로 컬럼 선택/그룹핑/정렬/시각화 연습에 초점을 맞춘 2차 노트북입니다
  (노트북 맨 앞 markdown 셀 참고). 예전에는 `src/EDA2.html`로 export되어 있었지만 그 파일은 이후
  정리 과정에서 삭제됐습니다 — 다시 필요하면 `jupyter nbconvert --to html`로 재생성하세요.
- `src/ai4i2020.csv`(10,000행 × 14열)는 결측치·중복행이 없지만, `Type`과 `Product ID`에 앞뒤 공백이 섞여
  있어 groupby/join 전에 반드시 strip해야 합니다 (`EDA2.ipynb` 초반의 `.str.strip()` 호출 참고).
- 이후 모델링 작업에 참고해야 할 분석 결과(`README.md` 기준):
  - 타겟 `Machine failure`의 클래스 불균형이 심함(양성 3.39%) — accuracy 대신 recall/precision/F1/ROC-AUC
    사용, 리샘플링(SMOTE)이나 `class_weight` 고려.
  - 강한 다중공선성: `Air temperature` ↔ `Process temperature` (+0.88), `Rotational speed` ↔ `Torque`
    (−0.88) — 선형모델/특성 선택 시 유의.
  - 5개 세부 고장 모드 플래그(`TWF`, `HDF`, `PWF`, `OSF`, `RNF`)가 `Machine failure`와 완전히 일치하지 않음
    (불일치 27건) — 원본 라벨링이 100% 결정론적이지 않으며, 특히 `RNF`가 그러함.
  - 고장 예측에 가장 유효한 변수: `Torque` > `Tool wear` > `Air temperature`; 제품 `Type` 등급이 높을수록
    고장률이 낮아짐 (L 3.92% > M 2.77% > H 2.09%).

### (삭제됨) `classifications.ipynb` — `Type`(품질 등급) 분류 모델 4종 비교
> **이 노트북 파일은 더 이상 저장소에 없습니다** (위 "파일 이름 변경/삭제 이력" 참고). 아래 내용은
> 실행 당시의 접근 방식/결론을 참고용으로 남겨둔 것이며, 결과 요약은 `README.md` 2-1절에도 있습니다.
> 이 실험을 다시 하고 싶으면 이 절의 설명대로 새로 노트북을 만들면 됩니다.

`ai4i2020.csv`의 센서값(`Air/Process temperature`, `Rotational speed`, `Torque`, `Tool wear`)과
`Machine failure`/세부 고장 모드(`TWF`/`HDF`/`PWF`/`OSF`/`RNF`)로 `Type`(L/M/H)을 예측하는 다중분류
문제를 다룹니다. `UDI`/`Product ID`는 식별자라 특성에서 제외했습니다.

- **전처리**: `EDA2.ipynb`와 동일하게 컬럼명과 `Type`/`Product ID`의 앞뒤 공백을 strip. 특성 컬럼명은
  `Air_temperature`처럼 대괄호/공백을 제거한 이름으로 다시 rename합니다 — XGBoost의 `DMatrix`가 컬럼명에
  `[`, `]`, `<` 문자를 허용하지 않기 때문(`docs/troubleshooting.md` 참고). 타겟은 `LabelEncoder`로 L/M/H를
  0/1/2로 인코딩.
- **파생변수 4개**: `Temp_diff`(`Process_temperature`−`Air_temperature`, 온도차 — HDF 판정 기준과 연결),
  `Power`(`Torque`×`Rotational_speed`를 rad/s로 환산한 기계 동력[W] — 회전속도/토크의 강한 역상관을
  하나의 신호로 압축), `Torque_x_ToolWear`(`Torque`×`Tool_wear` — OSF 과부하 판정 임계값이 Type별로
  다르다는 점(L=11,000/M=12,000/H=13,000)에 착안), `Failure_mode_count`(TWF+HDF+PWF+OSF+RNF 합, 동시
  발생한 고장 모드 개수). 행 단위 결정론적 변환이라 train/test 분리 전에 만들어도 데이터 누수가 아님.
- **모델 4종**: `RandomForestClassifier`, `XGBClassifier`, `LogisticRegression`, `SVC(probability=True)`.
  `Type` 분포가 L(60%)/M(30%)/H(10%)로 치우쳐 있어 `class_weight="balanced"`(XGBoost는
  `compute_sample_weight`로 만든 `sample_weight`)를 적용. `LogisticRegression`/`SVC`는 `StandardScaler`로
  표준화한 데이터를, `RandomForestClassifier`/`XGBClassifier`는 원본 스케일 데이터를 사용합니다(트리
  기반 모델은 스케일링이 불필요).
- **평가지표**: 정확도, 정밀도/재현율/F1-score(전부 `average="macro"`, 3-클래스 다중분류라서), AUC는
  `roc_auc_score(..., multi_class="ovr", average="macro")`. 모델별 `classification_report`와 혼동행렬도
  같이 출력합니다.
- **그래프**: 모델별 ROC Curve(2x2 서브플롯, 클래스별 One-vs-Rest 곡선 + macro-average 곡선)를
  `../images/model_roc_curves.png`에, 모델별 F1-score(macro) 비교 막대그래프를
  `../images/model_f1_comparison.png`에 저장.
- **핵심 결과(실행해서 확인한 값, 재실행하면 랜덤성 때문에 약간 달라질 수 있음)**: 파생변수 포함 기준
  F1(macro)은 XGBoost(0.328) > Random Forest(0.325) > Logistic Regression(0.233) > SVM(0.218),
  AUC(macro)는 Random Forest(0.509) > XGBoost(0.503) > Logistic Regression(0.497) > SVM(0.478)로 전
  모델이 **사실상 랜덤 수준**입니다(파생변수를 추가하기 전과 거의 동일 — F1/AUC 모두 소수점 둘째 자리
  안에서만 오르내림). 즉 물리적으로 그럴듯한 파생변수를 넣어도 `Type`(품질 등급) 예측력은 거의 개선되지
  않습니다 — `Type`이 가동 중 센서 측정값과 직접적 인과관계가 없는 식별자성 라벨에 가깝다는 뜻으로
  해석됩니다. 다만 Random Forest 특성 중요도에서는 `Power`/`Torque_x_ToolWear`가 이들을 만든 원본
  변수(`Rotational_speed`/`Torque`/`Tool_wear`)보다 오히려 더 높게 나와, 파생변수가 원본보다 정보를 조금
  더 압축해서 담고 있다는 점은 확인됩니다(전체 성능 개선으로 이어질 정도는 아님). 이후 이 노트북을
  고치거나 새 모델링 코드를 짤 때 "특성을 더 정교하게 손보면 이 결과가 크게 개선될 것"이라고 가정하지
  말고, 먼저 이 결론(약한 신호)을 참고하세요.

### (삭제됨) `regression.ipynb` — Torque[Nm] 회귀 모델 4종 비교
> **이 노트북 파일도 더 이상 저장소에 없습니다** (위 "파일 이름 변경/삭제 이력" 참고). 결과 요약은
> `README.md` 2-2절 참고.

`classifications.ipynb`(Type 분류)와 짝을 이루는 회귀 버전. `Air/Process temperature`, `Rotational
speed`, `Tool wear`, `Machine failure`/고장 모드 플래그로 `Torque [Nm]`을 예측한다. **주의**:
`Rotational speed`는 특성으로 써도 되지만(EDA에서 확인한 -0.88 상관관계), `Power`나
`Torque × Tool wear`처럼 `Torque`를 직접 곱해 만드는 파생변수는 타겟 정보를 그대로 포함하므로(데이터
누수) 이 노트북에서는 만들지 않는다.

- **모델 4종**: `RandomForestRegressor`, `XGBRegressor`, `LinearRegression`, `SVR(kernel="rbf")`.
  Linear Regression/SVR은 `StandardScaler`로 표준화한 데이터를, 트리 기반 모델은 원본 데이터를 사용.
- **평가지표**: R², MAE, RMSE, MAPE(%).
- **그래프**: 모델별 "실제값 vs 예측값" 산점도(2x2, y=x 기준선 포함)를 `../images/regression_scatter.png`에
  저장.
- **핵심 결과**: R² 기준 Random Forest(0.847) > XGBoost(0.822) > SVR(0.816) > Linear
  Regression(0.804) — **4개 모델 모두 R² 0.8 이상으로 뚜렷하게 예측됨**. `classifications.ipynb`의 Type
  예측(AUC 0.48~0.51, 랜덤 수준)과 대비되는 결과로, "물리적으로 실제 관계가 있는 변수(Torque↔회전속도)는
  잘 예측되고, 관계가 약한 라벨(Type)은 잘 예측되지 않는다"는 일관된 패턴을 보여준다. 두 노트북을 같이
  보면 "모델을 더 좋은 걸 썼는가"보다 "타겟이 특성들과 실제로 관계가 있는가"가 예측 성능을 훨씬 크게
  좌우한다는 점을 대조적으로 확인할 수 있다.

### `src/model_1.ipynb` / `src/model_2.ipynb` — `Machine failure` 이진분류 draft 2종
`model_3.ipynb`로 완성되기 전의 초기 draft 노트북입니다. **markdown 설명 셀이 전혀 없고 코드만 있어서**,
아래 요약은 코드를 직접 읽어서 정리한 것입니다. 둘 다 현재 UI(`model_predictor.py`)와 연결돼 있지 않고,
과거 실험 기록으로만 남아 있습니다 — 새로 손볼 필요가 생기면 `model_3.ipynb`의 위험구간(zone) 피처를
먼저 적용해보는 쪽을 권장합니다.

- **`model_1.ipynb`**: `Product ID` 제거 + `Type` 원-핫 인코딩 → `MinMaxScaler` + `SMOTE`(RandomForest만
  SMOTE 적용 데이터로 학습, XGBoost/LightGBM은 원본 데이터로 학습) → RandomForest(`n_estimators=500,
  max_depth=15, class_weight="balanced"`)/XGBoost/LightGBM 단순 비교. 정확도 기준 RandomForest 0.942,
  XGBoost 0.984, LightGBM 0.9845.
- **`model_2.ipynb`**: `model_1.ipynb`과 같은 전처리에 파생변수(`Power` 등)를 추가하고,
  `RandomForestClassifier`에 `RandomizedSearchCV`(`scoring="recall"`, `n_iter=30`, `cv=5`, `n_jobs=-1`,
  커스텀 `class_weight` 딕셔너리 후보 포함)로 하이퍼파라미터 탐색을 수행. 재현율(recall) 기준 최적화라
  best recall이 약 0.995까지 나왔음(재현율에 치우친 튜닝이라 정밀도와의 트레이드오프는 별도 확인 필요).
  - **주의(실제로 겪은 버그, Windows 한정)**: `n_jobs=-1`처럼 `n_jobs`를 1이 아닌 값으로 주면, Windows
    사용자 폴더 이름에 한글(비-ASCII 문자)이 섞여 있을 때 joblib이 임시 폴더 경로를 ASCII로 인코딩하려다
    `UnicodeEncodeError`로 죽는다. 이 노트북 첫 셀에 `os.environ.setdefault("JOBLIB_TEMP_FOLDER", ...)`로
    ASCII 전용 시스템 임시 폴더를 지정해 회피해뒀다 — `n_jobs`를 쓰는 새 코드를 추가할 때 이 패턴을
    재사용할 것 (`docs/troubleshooting.md` 참고).

### `src/model_3.ipynb` — `Machine failure`(정상/불량) 이진분류, UI에 실제로 배포된 모델
확정 주제인 정상/불량 이진분류를 다루는 세 번째(최종) 모델링 노트북입니다 — `model_1.ipynb`/
`model_2.ipynb`의 draft를 이어받아 위험구간(zone) 피처 엔지니어링으로 완성한 버전이자, 실제로 UI에
배포된 모델(`model/random_forest_enhanced.joblib`)을 만들어내는 노트북입니다. **주의**: 노트북 파일명은
`model_3.ipynb`이지만 내부 markdown/`savefig()`/`joblib.dump()` 경로는 과거 이름인 `modeling2`를 그대로
쓰고 있습니다(`../images/modeling2_*.png`, `docs/modeling2_binary_eda.md`, 노트북 안내 문구의
`src/modeling2.ipynb`) — 리네임 후 내부 문구를 안 고친 상태이니 새로 셀을 추가할 때 파일명이 아니라
`modeling2_` 접두어 컨벤션을 그대로 따르면 됩니다(혼동 방지용으로만 알아두면 됨, 지금 당장 고칠 필요는
없음).

1. **데이터 로드/전처리** — `EDA2.ipynb`와 동일하게 컬럼명·`Type` 공백 strip, 식별자(`UDI`/`Product ID`)와
   타겟과 사실상 동치인 세부 고장 모드 컬럼(`TWF`~`RNF`) 제거.
2. **EDA** — `machine_failure` 클래스 불균형(불량 3.39%) 재확인, 원본/파생 변수별 정상·불량 박스플롯.
3. **피처 엔지니어링(위험구간 zone 플래그)** — `temp_diff`/`machanical_power`/`tool_stress`에 더해,
   AI4I 2020 공식 문서의 세부 고장 모드 임계값 규칙(라벨 자체가 아니라 원본 입력 변수로 재계산 — 데이터
   누수 아님)으로 `hdf_zone`/`pwf_zone`/`osf_zone`(Type별 임계값 L=11000/M=12000/H=13000)/`high_wear`
   4개 플래그와 이를 합산한 `risk_zone_count`(0~4)를 만듭니다. `risk_zone_count`가 원본 변수를 통틀어
   `machine_failure`와 가장 강한 상관관계를 보입니다. **`src/UI/model_predictor.py`의
   `build_feature_row()`가 이 계산을 그대로 재구현**하므로, 여기 로직을 고치면 그쪽도 같이 고쳐야
   합니다.
4. **모델링** — Random Forest/XGBoost/LightGBM × Baseline(원본 7개)/Enhanced(zone 포함 15개) 총 6가지
   조합 비교. zone 피처 추가 효과는 3개 모델 전부에서 재현됨(F1 상승). **Enhanced 피처셋의 Random
   Forest**가 F1 0.912·정밀도 1.000·재현율 0.838·AUC 0.973로 6개 조합 중 가장 좋습니다.
5. **결론** — 6개 조합 지표 표 + 해석(`docs/modeling2_binary_eda.md`에도 정리).
6. **모델 저장** (**구현 완료**) — 5번에서 가장 좋았던 Random Forest(Enhanced)를
   `../model/random_forest_enhanced.joblib`에 저장합니다. 4-1 학습 루프가 `feature_sets`를
   `{"Baseline", "Enhanced"}` 순서로 돌기 때문에 루프가 끝난 시점의 `models["Random Forest"]`가 곧
   Enhanced로 학습된 RF라는 점을 이용합니다. `joblib.dump()`로 `{"model": ..., "features": enhanced_cols,
   "metrics": eval_results["Random Forest (Enhanced)"]}`를 같이 저장해서, `model_predictor.py`가 예측에
   쓸 피처 순서와 "모델 훈련 결과 보기" 탭에 보여줄 지표를 모델 파일 하나에서 전부 읽어가게 합니다.

### `src/UI/main.py` — Tkinter 데스크톱 UI 셸 (UI 전용, 크롤링/그래프 내용은 모른다)
하나의 `Frame` 안에서 `grid`로 좌/우를 나눈 단일 파일 앱입니다. **`main.py`는 위젯 조립만 담당하고, "무엇을
그릴지"/"무엇을 어떻게 수집할지"는 전혀 알지 못합니다** — 그래프는 `visualizer.py`의 `Visualizer`, 크롤링은
`crawler.py`의 `DataCrawler`에 위임합니다.

- **오른쪽 패널 (동작함, 왼쪽 그래프와 연결됨):** 네이버 뉴스 대시보드. `__init__`에서 만든
  `self._crawler = DataCrawler()` 인스턴스를 재사용하며, `_load_news_worker()`가 Tk 메인루프를 막지 않도록
  백그라운드 `threading.Thread`에서 `self._crawler.fetch_news_items()`를 호출하고 `crawler.CRAWL_ERRORS`로
  실패를 잡습니다. 결과 콜백은 직접 `self.after(...)`를 부르지 않고 `_schedule_on_ui_thread(callback, *args)`
  를 거칩니다 — 크롤링이 끝나기 전에 창이 닫히면 Tk 인터프리터가 이미 종료돼 `self.after()`가
  `RuntimeError`를 던지는데, 이 헬퍼가 그 경우를 조용히 무시합니다 (`docs/troubleshooting.md` 참고).
  **백그라운드 스레드에서 Tk 위젯을 건드리는 새 코드를 추가할 때는 이 헬퍼를 재사용하세요.** 기사 제목을
  클릭하면 `crawler.open_in_chrome()`이 호출되며, `PROGRAMFILES`/`PROGRAMFILES(X86)`/`LOCALAPPDATA`에서
  Chrome을 찾고 없으면 `webbrowser.open_new_tab`으로 대체합니다.
  - **동시에 여러 검색 요청이 진행 중일 수 있다.** 그래프 카드를 빠르게 연달아 클릭하면 `refresh_news()`가
    매번 새 스레드를 띄우는데, 먼저 시작한 느린 요청이 나중에 시작한 빠른 요청보다 늦게 끝날 수 있습니다.
    `self._news_request_id`(요청마다 증가하는 카운터)와 `_apply_if_current(request_id, callback, arg)`가
    이를 가드합니다 — `request_id`가 `self._news_request_id`와 다르면(더 최신 요청이 이미 시작됐으면) 그
    결과는 조용히 버려집니다. `_load_news_worker(request_id)`가 이 가드를 거쳐 `_show_news`/`_show_error`를
    예약합니다 (`docs/troubleshooting.md` 참고). **사용자가 빠르게 여러 번 트리거할 수 있는 새 백그라운드
    작업(예: 나중의 모델 예측 호출)을 추가할 때도 이 "최신 요청만 반영" 패턴을 재사용하세요.**
  - **검색어는 고정이 아니라 왼쪽 그래프 카드가 정한다.** `self._crawler.search_word`의 초깃값은
    `DataCrawler()`의 기본값("CNC 불량")이지만, 그래프 카드를 클릭하면 `_search_news_for_chart(chart_title,
    keyword)`가 `self._crawler.search_word`를 그 차트의 `chart_specs()` 4번째 값(검색 키워드)으로 바꾸고
    `self.news_subtitle_var`(오른쪽 패널 부제목 `tk.StringVar`)를 갱신한 뒤 `self.refresh_news()`를 호출해
    다시 크롤링합니다 — "이 그래프가 보여주는 인사이트와 관련된 뉴스"를 찾아보는 용도입니다. 검색어 자체를
    바꾸고 싶다면 `main.py`가 아니라 `visualizer.py`의 `chart_specs()`에서 해당 차트의 키워드를 고치세요.
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
      `(제목, plot_fn, 설명, 검색 키워드)` 목록을 순서대로 2열 그리드에 배치합니다. 각 카드는
      `_create_chart_card()`로 만들고, 카드마다 별도의 `matplotlib` `Figure`를 만들어 `plot_fn(figure,
      axes)`를 호출한 뒤 `FigureCanvasTkAgg`로 붙입니다. **어떤 그래프를 보여줄지, 몇 개인지, 설명 문구와
      검색 키워드는 무엇인지는 전부 `visualizer.py` 쪽 책임** — 그래프를 추가/제거/수정하려면 `main.py`가
      아니라 `Visualizer.chart_specs()`를 고치면 됩니다.
    - **그래프 카드를 클릭하면 설명 툴팁이 뜨고, 동시에 오른쪽 뉴스 패널이 그 차트의 키워드로 다시
      검색된다.** 카드나 제목을 클릭하면 `_toggle_chart_tooltip()`이 (a) `_open_chart_tooltip()`으로
      `overrideredirect(True)` `Toplevel`(테두리 없는 작은 박스, 팝업 창이 아님)을 클릭 지점 근처에 띄워
      `chart_specs()`의 설명 문구를 보여주고, (b) `_search_news_for_chart(title, keyword)`를 호출해 오른쪽
      패널을 그 차트의 인사이트와 관련된 뉴스로 갱신합니다 — 단, **새로 열 때만** 검색을 트리거합니다
      (같은 카드를 다시 클릭해 닫기만 할 때는 재검색하지 않음). 같은 카드를 다시 클릭하면 툴팁이 닫히고,
      다른 카드를 클릭하면 그쪽 설명/검색어로 바뀌며, 카드 밖(윈도우 배경)을 클릭하거나 그래프 영역을
      스크롤하거나 다른 nav 화면으로 전환하면(`_clear_data_box()`에서 처리) 툴팁만 자동으로 닫힙니다
      (뉴스 패널의 마지막 검색 결과는 유지됨). 카드 쪽 클릭 핸들러가 `"break"`를 반환해,
      `self.bind("<Button-1>", ...)`으로 걸어둔 "빈 곳 클릭 시 닫기" 바인딩과 충돌하지 않도록 되어 있습니다
      — 새로운 클릭형 위젯을 추가할 때 이 패턴을 참고하세요.
  - `_show_training_result_view()` (**구현 완료**)는 `model_predictor.get_metrics()`로 배포된 모델
    (Random Forest, Enhanced 피처셋)의 정확도/정밀도/재현율/F1-score/AUC를 읽어 `_build_metric_tiles()`로
    요약 카드 5개를 그리고, `_build_training_chart_grid()`로 `model_3.ipynb`가 이미 만들어 둔 비교 그래프
    PNG 2장(`model_predictor.TRAINING_RESULT_CHARTS` — 모델 3종×피처셋 2종 지표 비교, 혼동행렬 비교)을
    보여줍니다. 6개 조합 전체가 아니라 **배포된 모델 하나만** 카드로 요약하고, 나머지 5개 조합과의
    비교는 이미지 안에 이미 다 들어있어 별도 표를 안 만들었습니다. `model/random_forest_enhanced.joblib`
    또는 `images/modeling2_*.png`가 없으면 `_show_data_error()`로 안내합니다 — 즉 숫자를 이 파일이나
    `main.py`에 하드코딩하지 않고, **모델 파일(`metrics` 키)을 지표의 단일 출처로 둡니다.**
  - **입력 `Entry` 6개는 "모델 입력하기" 탭에서만 보인다.** 예전에는 `_build_ui()`가 `input_row`를
    좌측 상단에 고정으로 항상 그렸지만, 지금은 그 자리에 아무것도 없고 `_show_model_input_view()`가
    `selected_index == 2`일 때만 `self.data_box` 안에 폼을 새로 그립니다. `MODEL_INPUT_NAMES =
    ("type", "air_temp", "proc_temp", "rot_speed", "torque", "tool_wear")`는 여전히 배치 순서이자 모델에
    전달될 실제 변수명(영문 유지 — 모델 피처 순서와 맞춰야 함)이고, **화면에 보이는 라벨만**
    `MODEL_INPUT_LABELS`(예: `"air_temp"` → `"기온"`) 딕셔너리로 한글로 표시합니다. 새 입력 필드를
    추가하면 `MODEL_INPUT_NAMES`뿐 아니라 `MODEL_INPUT_LABELS`에도 한글 라벨을 같이 채워야 합니다.
  - 이 탭의 흐름: `_show_model_input_view()`가 폼 + "입력값 저장" 버튼 + 요약 영역
    (`self._model_input_summary_area`) + 예측 결과 영역(`self._model_prediction_area`)을 그리고, 버튼을
    누르면(탭 전환 시 자동 저장이 아님) `_save_model_inputs()`가 6개 입력값을 `self.model_input_values`에
    담고 `self.<name>` 속성에도 동일한 값을 반영한 뒤 `_render_model_input_summary()`로 요약을 다시
    그리고 `_on_model_input_saved()`를 호출합니다 — **구현 완료**: `model_predictor.predict(values)`를
    호출해 배포된 Random Forest(Enhanced) 모델로 정상/불량과 불량 확률을 예측하고,
    `_render_prediction_result()`가 결과를 `STATUS_GOOD`/`STATUS_CRITICAL` 색으로 표시합니다.
    `values`(6개 축약 입력)를 모델이 실제로 쓰는 15개 피처(파생변수 포함)로 바꾸는 로직은 `main.py`가
    아니라 `model_predictor.build_feature_row()`에 있습니다(`model_3.ipynb` 3-1의 위험구간 계산과 완전히
    동일한 로직을 재사용 — 로직이 갈라지지 않도록 나중에 노트북 쪽 계산을 고치면 이 함수도 같이
    고쳐야 합니다). 빈 값/숫자가 아닌 값/L·M·H가 아닌 `type` 등은 `model_predictor.PREDICTION_ERRORS`로
    잡아 에러 메시지를 그대로 보여줍니다(예측은 크롤링과 달리 네트워크 지연이 없어 별도 스레드 없이
    버튼 클릭 시 동기로 실행). 입력값은 `self.model_input_vars`(탭 전환과 무관하게 살아있는
    `tk.StringVar`)에, 마지막 예측 결과/에러는 `self._last_prediction_result`/`self._last_prediction_error`
    에 보관되므로, 저장하지 않고 다른 탭에 갔다 와도 입력값과 예측 결과가 모두 유지됩니다.

### `src/UI/visualizer.py` — 그래프 전용 모듈 (Tkinter를 모른다)
`ai4i2020.csv`를 `matplotlib`으로 그리는 로직만 담당하며, Tkinter는 import조차 하지 않습니다. 흐름도가
지정한 `visualizer.py` / `Visualizer` 이름과 `plot_dist()`/`plot_corr()`/`plot_box()`/`plot_scatter()`
메서드 이름을 그대로 따랐습니다 (아래 "목표 파이프라인 모듈" 표 참고 — 이 모듈은 예정보다 먼저 구현됨).

- `Visualizer(dataframe)`으로 생성. 내부 상태는 `self.dataframe` 하나뿐입니다.
- `summarize_status()` — 전체/정상/불량 건수와 불량률 dict. UI 요약 카드가 그대로 소비합니다.
- `chart_specs()` — `(제목, plot_fn, 설명, 검색 키워드)` 튜플 12개. **"전체 데이터 한 눈에 보기"에 어떤
  차트를 몇 개, 무슨 순서, 무슨 설명·검색 키워드로 보여줄지는 이 메서드가 결정**합니다. 설명은 UI가 그래프
  카드를 클릭했을 때 툴팁으로 보여주는 한글 문장이고, **검색 키워드는 같은 클릭에서 오른쪽 뉴스 패널이
  검색할 문구**입니다 — 그 차트의 핵심 발견(가장 흔한 고장 모드, 가장 강한 상관관계 등)을 반영해서, 크롤링이
  "이 그래프가 알려주는 것과 실제 업계 뉴스가 같은 이야기를 하는지" 찾아보게 하는 용도입니다. 예:
  "세부 고장 모드별 발생 건수" 차트는 데이터에서 가장 흔한 고장 모드가 HDF(방열)이므로 키워드가
  `"CNC 방열 고장"`입니다. 그래프를 추가/수정할 때 설명과 검색 키워드를 반드시 같이 채워야 합니다. 각
  `plot_fn`은 `plot_fn(figure, axes)` 시그니처로, 흐름도의 4개 범용 메서드를 구체적인 컬럼에 바인딩한
  람다이거나 전용 메서드입니다:
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

### `src/UI/crawler.py` — 크롤링 전용 모듈 (Tkinter를 모른다)
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

### `src/UI/model_predictor.py` — 예측 전용 모듈 (Tkinter를 모른다)
`src/model_3.ipynb`가 저장한 학습된 모델을 불러와 예측/평가지표를 돌려주는 로직만 담당하며, `crawler.py`/
`visualizer.py`처럼 Tkinter는 import조차 하지 않습니다.

- `MODEL_PATH` — 저장소 루트 `model/random_forest_enhanced.joblib`을 가리킵니다. 이 파일은
  `{"model": RandomForestClassifier, "features": [...15개 컬럼명...], "metrics": {...}}` 형태의
  딕셔너리이며, `model_3.ipynb`의 "6. 모델 저장" 셀이 만듭니다(4-1 학습 루프의 마지막 반복인 Enhanced
  피처셋 상태가 그대로 남아 있는 걸 이용 — `models["Random Forest"]`가 곧 Enhanced로 학습된 RF).
- `load_artifact()` — joblib 파일을 최초 1회만 읽어 모듈 전역에 캐시합니다. 파일이 없으면
  `FileNotFoundError`(어떤 노트북을 먼저 실행해야 하는지 안내하는 메시지 포함)를 던집니다.
- `get_metrics()` — 저장된 `metrics`(정확도/정밀도/재현율/F1-score/AUC, 한글 키)를 그대로 반환합니다.
  "모델 훈련 결과 보기" 탭이 이 값을 그대로 쓰므로, **지표 숫자를 `main.py`나 이 문서에 하드코딩하지
  않고 모델 파일 자체를 단일 출처로 둡니다** — 나중에 노트북을 재실행해 모델이 바뀌면 숫자도 자동으로
  같이 바뀝니다.
- `build_feature_row(values)` — `main.py`의 `MODEL_INPUT_NAMES` 6개 축약 입력(문자열 dict)을 모델이
  실제로 학습한 15개 피처(원본 5개 + `Type` 원-핫 2개 + `model_3.ipynb` 3-1과 동일한 파생변수
  `temp_diff`/`machanical_power`/`tool_stress`/`hdf_zone`/`pwf_zone`/`osf_zone`/`high_wear`/
  `risk_zone_count`)로 변환한 1행짜리 `DataFrame`을 만듭니다. 컬럼 순서는 하드코딩하지 않고 저장된
  `features` 목록을 그대로 따릅니다. 빈 값/숫자 변환 실패/`type`이 L·M·H가 아님을 각각 검증해
  `ValueError`로 던집니다.
- `predict(values)` — `build_feature_row()` + `model.predict()`/`predict_proba()`를 실행해
  `{"label": "정상"/"불량", "is_failure": bool, "failure_probability": float}`을 반환합니다.
- `PREDICTION_ERRORS` — `main.py`가 예측 실패를 잡을 때 쓰는 예외 튜플(`FileNotFoundError`,
  `ValueError`, `KeyError`) — `crawler.CRAWL_ERRORS`와 같은 패턴입니다.
- `TRAINING_RESULT_CHARTS` — "모델 훈련 결과 보기" 탭이 보여줄 `(제목, 이미지 경로, 설명)` 튜플 목록.
  `model_3.ipynb`가 이미 만들어 둔 `images/modeling2_model_comparison.png`/
  `images/modeling2_confusion_matrices.png`를 가리킵니다 — 새 비교 그래프를 추가하려면 노트북에서 먼저
  이미지를 만들고 이 튜플에 추가하세요.
- 이 모듈이 계산하는 위험구간 파생변수 로직은 `model_3.ipynb` 3-1과 **완전히 동일해야** 합니다. 노트북
  쪽 계산식(임계값, AND/OR 조건 등)을 고치면 이 파일의 `build_feature_row()`도 반드시 같이 고치세요 —
  두 곳이 어긋나면 노트북에서 학습한 모델과 UI가 실제로 넣어주는 입력이 서로 달라집니다.

### 목표 파이프라인 모듈 (`미니 프로젝트 흐름도.png` 기준)
나중에 파이프라인의 나머지를 만들 때는, 새 이름을 만들지 말고 흐름도가 지정한 아래 모듈/클래스/함수
구성을 따라야 `main.py`의 UI 연결 지점들과 자연스럽게 이어집니다:

| 파일 | 클래스 | 메서드 | 상태 |
| --- | --- | --- | --- |
| `crawler.py` | `DataCrawler` | `collect()`, `parse()`, `save_raw()` | `collect()`/`parse()` **구현 완료** (위 절 참고), `save_raw()`는 미구현·보류 |
| `preprocessor.py` | `Preprocessor` | `load()`, `clean_missing()`, `encode()`, `scale()`, `feature_engineering()`, `save_processed()` | 미구현, 보류 |
| `visualizer.py` | `Visualizer` | `plot_dist()`, `plot_corr()`, `plot_box()`, `plot_scatter()` | **구현 완료** (위 절 참고) |
| `literacy.py` | `Literacy` | `ask_question()`, `analyze()`, `answer_qa()` | 미구현, 보류 |
| `modeling.py` | `Modeler` | `train()`, `predict()`, `save_model()` | 미구현, 보류 — 단, `train()`/`save_model()`에 해당하는 작업은 `src/model_3.ipynb`가, `predict()`에 해당하는 작업은 `src/UI/model_predictor.py`가 이 모듈 밖에서 이미 수행 중 (아래 두 절 참고). 나중에 `modeling.py`를 만들 때는 이 둘의 로직을 옮기는 리팩터링에 가깝습니다. |
| `evaluation.py` | `Evaluator` | `classification_metrics()`, `regression_metrics()`, `plot_confusion()` | 미구현, 보류 |
| `report.py` | (모듈 함수) | `make_report()`, `save_html()`, `save_pdf()` | 미구현, 보류 |

흐름도가 명시한 산출물: `processed.csv`(전처리된 데이터), `model.joblib`(학습된 모델), `report.html` /
`report.pdf`(자동 생성 보고서), `run.log`(실행 로그). 흐름도는 또한 기본적인 입력/전처리/모델 검증도
요구합니다(입력 단계: CSV 형식 및 필수 컬럼 검증; 전처리 후: 결측치/이상치/인코딩 확인; 학습 후: 교차검증
점수 및 train/test 과적합 확인). 크롤링/전처리/모델링/저장 단계별 예상 에러 케이스와 대응 방법을 정리한
표도 있으니, 파이프라인 코드를 새로 추가하기 전에 확인해 볼 가치가 있습니다 — 이 프로젝트가 맞춰야 할
에러 처리 수준을 정의하고 있기 때문입니다.
