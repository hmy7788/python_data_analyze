# AI4I 2020 Predictive Maintenance Dataset - EDA

- [UCI AI4I 2020 Predictive Maintenance Dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset) 기반 탐색적 데이터 분석(EDA) + 예측 모델링 프로젝트
- 분석 코드: [`src/EDA.ipynb`](src/EDA.ipynb)
- 원본 데이터: [`src/ai4i2020.csv`](src/ai4i2020.csv) (10,000행 x 14열)

## 데이터 개요

| 컬럼 | 설명 | 타입 |
| --- | --- | --- |
| UDI, Product ID | 식별자 | 정수, 문자열 |
| Type | 제품 품질 등급 (L: 저가, M: 중가, H: 고가) | 문자 |
| Air temperature [K] | 대기 온도 | 실수 |
| Process temperature [K] | 공정 온도 | 실수 |
| Rotational speed [rpm] | 회전 속도 | 정수 |
| Torque [Nm] | 토크 | 실수 |
| Tool wear [min] | 공구 사용 시간(마모도) | 정수 |
| Machine failure | 고장 여부 (타겟, 0/1) | 정수(0, 1) |
| TWF / HDF / PWF / OSF / RNF | 세부 고장 모드: 공구마모 / 방열 / 전력 / 과부하 / 랜덤 | 정수(0, 1) |

## 주요 분석 결과

### 1. 데이터 품질
- 결측치 없음, 중복행 없음

### 2. 수치형 변수 분포
![histograms](images/eda_histograms.png)

- Air temperature / Process temperature / Torque: 정규분포에 근접
- Rotational speed: 오른쪽 꼬리가 긴 분포
- Tool wear: 0~253분, 비교적 고르게 분포

### 3. Type(품질 등급) 분포
![type dist](images/eda_type_dist.png)

- L(60%) > M(30%) > H(10%)

### 4. 타겟(Machine failure) 분포 — 클래스 불균형
![failure dist](images/eda_failure_dist.png)

- 정상 9,661건(96.6%) vs 고장 339건(**3.39%**)
- 극심한 클래스 불균형
- → 모델링 시 accuracy 대신 recall / precision / F1 / ROC-AUC 사용
- → 리샘플링(SMOTE) 또는 class_weight 조정 필요

### 5. 세부 고장 모드 (TWF, HDF, PWF, OSF, RNF)
![failure modes](images/eda_failure_modes.png)

- 발생 빈도: **HDF(방열, 115건) > OSF(과부하, 98건) > PWF(전력, 95건) > TWF(공구마모, 46건) > RNF(랜덤, 19건)**
- 대부분 세부 모드 1개만 발생, 2~3개 동시 발생 케이스도 존재
- 데이터 불일치 확인
  - `Machine failure=1`인데 세부 모드 없음: 9건
  - `Machine failure=0`인데 세부 모드 있음: 18건
  - → 라벨링 규칙(특히 RNF)이 100% 결정론적이지 않음, 전처리 시 유의

### 6. 상관관계
![corr heatmap](images/eda_corr_heatmap.png)

- `Air temperature` ↔ `Process temperature`: **+0.88** (강한 양의 상관 → 다중공선성 주의)
- `Rotational speed` ↔ `Torque`: **-0.88** (강한 음의 상관 → 일정 출력 가정 시 당연한 물리적 관계)
- `Machine failure` 상관 순위: `Torque`(0.19) > `Tool wear`(0.11) > `Air temperature`(0.08)

### 7. 고장 여부에 따른 변수 분포
![boxplot by failure](images/eda_boxplot_by_failure.png)

- 고장 발생 시 `Torque`·`Tool wear` 대체로 높음, `Rotational speed`는 낮은 경향
- 토크-회전속도 역상관과 일치

### 8. Type(품질 등급)별 고장률
![failrate by type](images/eda_failrate_by_type.png)

| Type | 총건수 | 고장건수 | 고장률 |
| --- | --- | --- | --- |
| L (저가) | 6,000 | 235 | 3.92% |
| M (중가) | 2,997 | 83 | 2.77% |
| H (고가) | 1,003 | 21 | 2.09% |

- 등급 낮을수록(L) 고장률 높음, 등급 높을수록(H) 고장률 낮음
- → 저가형 제품의 내구성/공차가 상대적으로 낮은 것으로 해석

## 정상/불량 판별 — 피처 엔지니어링으로 성능 끌어올리기

- 대상: `Machine failure`(0=정상, 1=불량) — 이진분류
- 코드: [`src/modeling2.ipynb`](src/modeling2.ipynb)
- 상세 과정/그래프: [`docs/modeling2_binary_eda.md`](docs/modeling2_binary_eda.md)
- 목표 설정 근거: EDA에서 `Torque`/`Tool wear`와 상관관계가 확인된 타겟 → 설비진단 문제로 직결

**배경 — 클래스 불균형**
- 정상 9,661건 vs 불량 339건(3.4%), EDA와 동일한 불균형

**피처 엔지니어링 — 위험구간(zone) 플래그**
- 근거: UCI 공식 데이터셋 설명에 정의된 고장 발생 조건(임의 추정 아님)
- 비유: 자동차 계기판 경고등 — 특정 조건 진입 시 경고등 점등

| 피처 | 점등 조건 | 의미 |
| --- | --- | --- |
| `hdf_zone` | 온도차 < 8.6K **AND** 회전속도 < 1380rpm | 방열 고장 위험 |
| `pwf_zone` | 동력 < 3500W **OR** 동력 > 9000W | 전력 고장 위험 |
| `osf_zone` | 토크×공구마모 > Type별 임계값(L11000/M12000/H13000) | 과부하 위험 |
| `high_wear` | 공구마모 > 200분 | 공구마모 고장 임박 |
| `risk_zone_count` | 위 4개 합산(0~4) | 동시 점등 개수 |

![위험구간 개수 vs 불량률](images/modeling2_risk_zone_failure_rate.png)

- `risk_zone_count`별 실제 불량률: 0개 → 0.11% / 1개 → 27.2% / 2개 이상 → 100%
- → 경고등 2개 이상 동시 점등 시 사실상 고장 확정

**모델 비교 — Baseline(원본 변수만) vs Enhanced(위험구간 추가)**
- 검증 모델 3종: Random Forest, XGBoost, LightGBM (특정 모델만의 우연 여부 확인 목적)

| 모델 | Baseline (F1) | Enhanced (F1) | 개선폭 |
| --- | --- | --- | --- |
| Random Forest | 0.727 | **0.912** | +0.185 |
| XGBoost | 0.756 | 0.884 | +0.128 |
| LightGBM | 0.800 | 0.898 | +0.098 |

![모델 3종 x Baseline/Enhanced 지표 비교](images/modeling2_model_comparison.png)

**해석**
- 3개 모델 전부 개선 → 특정 모델 한정 효과 아닌 일반적 효과
- Baseline 기준 LightGBM 최고 → 그래디언트 부스팅 계열이 조합 규칙을 어느 정도 자체 탐지
- Random Forest 개선폭 최대 → 원래 조합 규칙 탐지력이 가장 약했던 모델이 위험구간 피처 효과를 가장 크게 흡수
- AUC는 6개 조합 전부 0.970~0.974로 거의 동일 → 위험구간 피처는 "순위 매기기(AUC)"보다 "정확한 경계 판별(precision/recall/F1)"에 기여

**핵심 요약**
1. 원본 변수 절대값보다 "위험 신호 동시 발생 개수"가 훨씬 강한 신호
2. 근거 기반 피처 엔지니어링 — 데이터셋 공식 문서의 고장 조건을 그대로 피처화
3. 클래스 불균형 문제는 AUC만으로 판단 금지 → F1/precision/recall 함께 확인 필요

## 실행 방법

```bash
pip install pandas numpy matplotlib seaborn jupyter scikit-learn xgboost lightgbm
jupyter nbconvert --to notebook --execute --inplace src/EDA.ipynb
jupyter nbconvert --to notebook --execute --inplace src/modeling2.ipynb
```
