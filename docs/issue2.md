# 에러 제목

컬럼 이름에 대괄호(`[`, `]`)가 있으면 XGBoost가 거부하는 에러 (`ValueError: feature_names must be string, and may not contain [, ] or <`)

```python
model = XGBClassifier()
model.fit(X_train, y_train)
```

```
ValueError: feature_names must be string, and may not contain [, ] or <
```

Random Forest, Logistic Regression 등 다른 모델은 같은 데이터로 문제없이 학습됐는데, XGBoost만 이 에러로 멈춤.

# 문제 원인 분석

- **발생 위치**: `src/classifications.ipynb`, `XGBClassifier().fit(X_train, y_train)` 호출부
- **발생 조건**: 원본 CSV의 컬럼 이름을 그대로 특성(feature)으로 사용해 XGBoost를 학습시킬 때
- **에러 메시지**: `ValueError: feature_names must be string, and may not contain [, ] or <`
- **추정 원인**: 원본 데이터의 컬럼 이름이 `"Air temperature [K]"`, `"Torque [Nm]"`처럼 단위를 대괄호로 표기하고 있음. XGBoost는 내부적으로 컬럼 이름을 특수한 형식(DMatrix)으로 바꿔서 쓰는데, 이 형식이 `[`, `]`, `<` 같은 문자를 이름에 쓰지 못하게 막아놓음. 다른 모델들은 이런 제약이 없어서 같은 컬럼 이름을 그대로 받아들였기 때문에, XGBoost에서만 에러가 난 것

# 문제 해결 방법

모델에 넣기 전에 컬럼 이름에서 대괄호와 공백을 없앤 이름으로 한 번에 바꿔줌.

# 수정한 코드

```python
# 기존 (문제 발생) — 원본 컬럼명을 그대로 사용
X = df[["Air temperature [K]", "Torque [Nm]", ...]]
model = XGBClassifier()
model.fit(X, y)  # ValueError 발생

# 수정 — 대괄호/공백 없는 이름으로 통일 후 사용
X = X.rename(columns={
    "Air temperature [K]": "Air_temperature",
    "Torque [Nm]": "Torque",
    # ...
})
model = XGBClassifier()
model.fit(X, y)  # 정상 동작
```

# 문제 해결 결과

컬럼 이름을 바꾼 뒤 `XGBClassifier().fit()`이 에러 없이 정상적으로 학습을 마쳤고, 이후 예측/평가까지 문제없이 진행됨.

# 결과

- pandas 컬럼 이름을 그대로 XGBoost에 넘기기 전에는 `[`, `]`, `<` 같은 특수문자가 있는지 항상 확인하기로 함
- 원본 CSV 컬럼명을 그대로 쓰지 않고, 모델링 전에 한 번 정리된 이름(`Air_temperature`, `Torque` 등)으로 바꿔 모든 모델에 동일하게 적용하는 습관을 들이기로 함
