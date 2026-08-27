"""학습된 Random Forest(Enhanced) 모델을 불러와 예측/평가지표를 돌려주는 순수 모듈.

`crawler.py`/`visualizer.py`와 같은 컨벤션으로, Tkinter는 import조차 하지 않는다.
`model_3.ipynb`의 "6. 모델 저장" 셀이 만든 `model/random_forest_enhanced.joblib`
(`{"model": ..., "features": [...], "metrics": {...}}`)을 그대로 읽어 쓴다.
"""

import math
from pathlib import Path

import joblib
import pandas as pd

# 이 파일은 src/UI/에 있고, model/ 폴더는 저장소 루트에 있다 (main.py의 DATA_PATH와 같은 패턴).
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "model" / "random_forest_enhanced.joblib"
# "모델 훈련 결과 보기" 탭이 보여줄, model_3.ipynb가 이미 만들어 둔 비교 그래프 2장.
IMAGES_DIR = Path(__file__).resolve().parent.parent.parent / "images"
TRAINING_RESULT_CHARTS = (
    (
        "모델 3종 x Baseline/Enhanced 지표 비교",
        IMAGES_DIR / "modeling2_model_comparison.png",
        "Random Forest/XGBoost/LightGBM을 Baseline(원본 변수)과 Enhanced(위험구간 피처 추가) "
        "두 피처셋으로 각각 학습했을 때의 정확도/정밀도/재현율/F1/AUC 비교. 배포된 모델은 "
        "이 중 Random Forest(Enhanced)이다.",
    ),
    (
        "혼동행렬 비교",
        IMAGES_DIR / "modeling2_confusion_matrices.png",
        "모델 3종 x 피처셋 2종 조합별 혼동행렬. Enhanced 피처를 추가하면 불량(1) 클래스의 "
        "오탐/누락이 눈에 띄게 줄어드는 것을 확인할 수 있다.",
    ),
)

# UI(main.py)에서 전달하는 값 중 숫자로 변환해야 하는 필드.
NUMERIC_FIELDS = ("air_temp", "proc_temp", "rot_speed", "torque", "tool_wear")
VALID_TYPES = ("L", "M", "H")
# Type별 OSF(과부하 고장) 임계값 — model_3.ipynb 3-1과 동일.
OSF_THRESHOLDS = {"L": 11000, "M": 12000, "H": 13000}

# main.py가 크롤링 실패를 CRAWL_ERRORS로 잡는 것과 같은 패턴.
PREDICTION_ERRORS = (FileNotFoundError, ValueError, KeyError)

_artifact_cache = None


def load_artifact():
    """joblib 파일을 최초 1회만 읽어 캐시한다. 파일이 없으면 안내 메시지와 함께 예외를 던진다."""
    global _artifact_cache
    if _artifact_cache is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}\n"
                "src/model_3.ipynb를 먼저 실행해 model/random_forest_enhanced.joblib을 생성해 주세요."
            )
        _artifact_cache = joblib.load(MODEL_PATH)
    return _artifact_cache


def get_metrics():
    """배포된 모델(Random Forest, Enhanced)의 평가지표 딕셔너리를 반환한다."""
    return load_artifact()["metrics"]


def _parse_float(values, field):
    raw = (values.get(field) or "").strip()
    if not raw:
        raise ValueError(f"'{field}' 값을 입력해 주세요.")
    try:
        return float(raw)
    except ValueError as error:
        raise ValueError(f"'{field}' 값이 숫자가 아닙니다: '{raw}'") from error


def build_feature_row(values):
    """UI의 6개 입력값(dict)을 model_3.ipynb와 동일한 파생 로직으로 15개 피처 1행으로 변환한다.

    컬럼 순서는 하드코딩하지 않고 joblib에 저장된 `features` 목록을 그대로 따른다 —
    나중에 모델을 다시 학습해 피처가 바뀌어도 이 함수는 고칠 필요가 없다.
    """
    machine_type = (values.get("type") or "").strip().upper()
    if machine_type not in VALID_TYPES:
        raise ValueError(f"품질 등급(type)은 L/M/H 중 하나여야 합니다: '{values.get('type', '')}'")

    air_temp = _parse_float(values, "air_temp")
    process_temp = _parse_float(values, "proc_temp")
    rotational_speed = _parse_float(values, "rot_speed")
    torque = _parse_float(values, "torque")
    tool_wear = _parse_float(values, "tool_wear")

    # model_3.ipynb 3-1(위험구간 플래그)과 완전히 동일한 계산.
    temp_diff = process_temp - air_temp
    machanical_power = torque * rotational_speed * (2 * math.pi / 60)
    tool_stress = torque * tool_wear
    hdf_zone = int(temp_diff < 8.6 and rotational_speed < 1380)
    pwf_zone = int(machanical_power < 3500 or machanical_power > 9000)
    osf_zone = int(tool_stress > OSF_THRESHOLDS[machine_type])
    high_wear = int(tool_wear > 200)
    risk_zone_count = hdf_zone + pwf_zone + osf_zone + high_wear

    row = {
        "air_temp": air_temp,
        "process_temp": process_temp,
        "rotational_speed": rotational_speed,
        "torque": torque,
        "tool_wear": tool_wear,
        "Type_L": int(machine_type == "L"),
        "Type_M": int(machine_type == "M"),
        "temp_diff": temp_diff,
        "machanical_power": machanical_power,
        "tool_stress": tool_stress,
        "hdf_zone": hdf_zone,
        "pwf_zone": pwf_zone,
        "osf_zone": osf_zone,
        "high_wear": high_wear,
        "risk_zone_count": risk_zone_count,
    }

    features = load_artifact()["features"]
    missing = [name for name in features if name not in row]
    if missing:
        raise KeyError(f"모델이 요구하는 피처를 계산하지 못했습니다: {missing}")

    return pd.DataFrame([[row[name] for name in features]], columns=features)


def predict(values):
    """UI 입력값(dict)으로 정상/불량을 예측한다.

    반환: {"label": "정상"/"불량", "is_failure": bool, "failure_probability": float}
    """
    artifact = load_artifact()
    model = artifact["model"]
    X = build_feature_row(values)

    prediction = int(model.predict(X)[0])
    failure_probability = float(model.predict_proba(X)[0][1])

    return {
        "label": "불량" if prediction == 1 else "정상",
        "is_failure": bool(prediction),
        "failure_probability": failure_probability,
    }
