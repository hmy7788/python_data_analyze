"""ai4i2020.csv에 결측치/중복행이 없다는 걸 확인하는 스크립트.

README.md "1. 데이터 품질" 항목("결측치 없음, 중복행 없음")의 근거 코드.
실행: 저장소 루트 또는 src/ 안에서 `python src/check_data_quality.py`
"""

import pandas as pd

df = pd.read_csv(r"src/ai4i2020.csv")
df.columns = [c.strip() for c in df.columns]  # 원본 컬럼명에 앞뒤 공백이 섞여있음 (예: ' Product ID')

print(f"전체 행/열 개수: {df.shape[0]}행 x {df.shape[1]}열\n")

# 1. 결측치 확인 — 컬럼별 결측치 개수
null_counts = df.isnull().sum()
print("컬럼별 결측치 개수:")
print(null_counts)
print(f"\n결측치 총합: {null_counts.sum()}건")

# 2. 중복행 확인 — 모든 컬럼 값이 완전히 같은 행
duplicate_count = df.duplicated().sum()
print(f"\n완전 중복행 개수: {duplicate_count}건")

# UDI/Product ID는 애초에 고유 식별자이므로, 그걸 빼고 나머지 컬럼 기준으로도 한 번 더 확인
duplicate_without_id = df.drop(columns=["UDI", "Product ID"]).duplicated().sum()
print(f"식별자(UDI/Product ID) 제외 중복행 개수: {duplicate_without_id}건")

print("\n=== 결론 ===")
if null_counts.sum() == 0 and duplicate_count == 0:
    print("결측치 없음, 중복행 없음 -> 전처리 부담이 적은 깨끗한 데이터셋")
else:
    print("결측치 또는 중복행이 존재함 -> 전처리 필요")
