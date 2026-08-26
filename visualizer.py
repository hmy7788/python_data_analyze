"""ai4i2020.csv 데이터로 "전체 데이터 한 눈에 보기" 그래프를 그리는 모듈.

Tkinter를 전혀 알지 못한다 (matplotlib Figure/Axes만 다룬다). UI 쪽(main.py)이
FigureCanvasTkAgg로 화면에 붙이는 역할을 맡고, 이 모듈은 "무엇을 어떻게 그릴지"만 책임진다.
클래스 이름과 plot_dist/plot_corr/plot_box/plot_scatter 메서드 이름은
`미니 프로젝트 흐름도.png`가 지정한 visualizer.py 스펙을 따른다.
"""

import matplotlib

# 한글 라벨이 깨지지 않도록 그래프용 폰트를 미리 지정한다.
matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

# 여러 그래프에서 공통으로 재사용하는 색상.
# 정상/불량 두 상태를 나타내는 그래프는 항상 이 두 색을 그대로 쓴다.
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"
SEQUENTIAL_BLUE = "#2a78d6"
DIVERGING_CMAP = "RdBu_r"
GRID_COLOR = "#E4E7EC"

CORRELATION_COLUMNS = (
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Machine failure",
)
CORRELATION_LABELS = ("기온", "공정온도", "회전속도", "토크", "공구마모", "고장")

# 세부 고장 모드 플래그. Machine failure=1인 행이 어떤 원인으로 실패했는지를 나타낸다.
FAILURE_MODE_COLUMNS = ("TWF", "HDF", "PWF", "OSF", "RNF")
FAILURE_MODE_LABELS = ("공구마모\n(TWF)", "방열\n(HDF)", "전력\n(PWF)", "과부하\n(OSF)", "랜덤\n(RNF)")


class Visualizer:
    """ai4i2020.csv 한 벌을 받아 "전체 데이터 한 눈에 보기" 그래프들을 그린다."""

    def __init__(self, dataframe):
        self.dataframe = dataframe

    def summarize_status(self):
        """전체/정상/불량 건수와 불량률을 담은 dict를 반환한다. UI 요약 카드에서 사용."""
        total = len(self.dataframe)
        failure_count = int(self.dataframe["Machine failure"].sum())
        normal_count = total - failure_count
        failure_rate = (failure_count / total * 100) if total else 0.0
        return {
            "total": total,
            "normal": normal_count,
            "failure": failure_count,
            "failure_rate": failure_rate,
        }

    def chart_specs(self):
        """(제목, 그리기 함수, 설명, 검색 키워드) 목록. 순서가 곧 "전체 데이터 한 눈에 보기" 화면의
        배치 순서다.

        각 그리기 함수는 plot_fn(figure, axes) 형태로 호출된다. 설명은 그래프를 클릭했을 때 UI가
        툴팁으로 보여줄 텍스트로, 차트가 무엇을 보여주는지를 한글로 요약한다. 검색 키워드는 같은
        클릭에서 오른쪽 뉴스 패널이 그 차트의 인사이트와 관련된 뉴스를 찾도록 넘기는 검색어다 —
        즉 크롤링이 "이 그래프가 알려주는 것과 실제 업계에서도 같은 이야기가 나오는지"를 찾아보게
        하는 용도이므로, 그 차트의 핵심 발견(가장 흔한 고장 모드, 가장 강한 상관관계 등)을 반영해야
        한다.
        """
        return (
            (
                "설비 상태 분포",
                self.plot_status_distribution,
                "정상과 불량 건수의 비율을 막대로 비교합니다. 불량 비율이 매우 낮아 "
                "클래스 불균형이 심한 데이터셋임을 보여줍니다.",
                "CNC 설비 불량률",
            ),
            (
                "품질 등급(Type) 분포",
                self.plot_type_distribution,
                "제품 품질 등급 L(저가)/M(중가)/H(고가)별 데이터 건수입니다. "
                "저가형(L) 제품이 전체의 약 60%로 가장 많습니다.",
                "CNC 저가형 장비 품질",
            ),
            (
                "Type별 불량률",
                self.plot_failure_rate_by_type,
                "품질 등급별 불량 발생 비율(%)입니다. 등급이 낮을수록(L) 불량률이 높고, "
                "등급이 높을수록(H) 낮아지는 경향을 보입니다.",
                "저가형 공작기계 고장",
            ),
            (
                "변수 간 상관관계",
                self.plot_corr,
                "수치형 변수들 사이의 상관계수(-1~1)를 색과 숫자로 함께 보여줍니다. "
                "진한 빨강/파랑일수록 상관관계가 강하며, 회전속도와 토크는 -0.88로 "
                "강한 음의 상관관계를 보입니다.",
                "CNC 회전속도 토크 관계",
            ),
            (
                "Torque 분포 (정상 vs 불량)",
                lambda figure, axes: self.plot_dist(figure, axes, "Torque [Nm]", "Torque [Nm]"),
                "정상(초록)과 불량(빨강) 상태별 Torque 값의 분포를 겹쳐서 비교합니다. "
                "불량 쪽이 전반적으로 더 높은 토크 값에 몰려 있습니다.",
                "CNC 토크 이상 고장",
            ),
            (
                "공구 마모(Tool wear) 분포 (정상 vs 불량)",
                lambda figure, axes: self.plot_dist(
                    figure, axes, "Tool wear [min]", "Tool wear [min]"
                ),
                "정상과 불량 상태별 공구 마모 시간의 분포입니다. 불량 쪽이 200분 이상 "
                "구간에서 뚜렷하게 몰려 있어, 공구 마모가 많이 진행될수록 불량 위험이 "
                "커짐을 시사합니다.",
                "CNC 공구 마모 교체",
            ),
            (
                "회전속도 vs 토크",
                lambda figure, axes: self.plot_scatter(
                    figure,
                    axes,
                    "Rotational speed [rpm]",
                    "Torque [Nm]",
                    "회전속도 [rpm]",
                    "Torque [Nm]",
                ),
                "회전속도와 토크의 관계를 산점도로 보여줍니다. 두 변수는 반비례 관계이며, "
                "불량(빨강) 포인트는 토크가 높거나 회전속도가 낮은 영역에 몰려 있습니다.",
                "CNC 회전속도 저하 원인",
            ),
            (
                "고장 여부별 Torque 비교",
                lambda figure, axes: self.plot_box(figure, axes, "Torque [Nm]", "Torque [Nm]"),
                "정상과 불량 상태의 Torque 값을 박스플롯으로 비교합니다. 불량 쪽의 중앙값과 "
                "분포가 정상보다 전반적으로 높습니다.",
                "CNC 과부하 고장",
            ),
            (
                "세부 고장 모드별 발생 건수",
                self.plot_failure_mode_counts,
                "Machine failure를 유발한 세부 원인별 건수입니다. 방열 실패(HDF)가 115건으로 "
                "가장 많고, 과부하(OSF) 98건, 전력 문제(PWF) 95건, 공구마모(TWF) 46건, "
                "랜덤 고장(RNF) 19건 순입니다.",
                "CNC 방열 고장",
            ),
            (
                "기온 vs 공정온도",
                lambda figure, axes: self.plot_scatter(
                    figure,
                    axes,
                    "Air temperature [K]",
                    "Process temperature [K]",
                    "기온 [K]",
                    "공정온도 [K]",
                ),
                "기온과 공정온도의 관계를 산점도로 보여줍니다. 두 변수는 +0.88의 강한 양의 "
                "상관관계를 가져, 모델링 시 다중공선성에 유의해야 합니다.",
                "CNC 공정온도 관리",
            ),
            (
                "회전속도 분포 (정상 vs 불량)",
                lambda figure, axes: self.plot_dist(
                    figure, axes, "Rotational speed [rpm]", "회전속도 [rpm]"
                ),
                "정상과 불량 상태별 회전속도의 분포입니다. 불량 쪽이 낮은 회전속도 구간에서 "
                "상대적으로 더 자주 나타나며, 이는 토크와의 반비례 관계와 일치합니다.",
                "CNC 저속 회전 이상",
            ),
            (
                "기온 분포 (정상 vs 불량)",
                lambda figure, axes: self.plot_dist(figure, axes, "Air temperature [K]", "기온 [K]"),
                "정상과 불량 상태별 기온의 분포입니다. 두 분포가 상당히 겹쳐 있어 기온 하나만으로는 "
                "불량 여부를 구분하기 어렵다는 것을 보여줍니다 (상관계수 0.08로 약함).",
                "CNC 설비 온도 영향",
            ),
        )

    @staticmethod
    def _style_axes(axes, grid_axis="y"):
        """카드형 차트 공통 스타일: 위/오른쪽 테두리 제거, 옅은 그리드, 작은 눈금 글씨."""
        axes.spines["top"].set_visible(False)
        axes.spines["right"].set_visible(False)
        axes.tick_params(labelsize=7)
        if grid_axis:
            axes.grid(axis=grid_axis, color=GRID_COLOR, linewidth=0.6, alpha=0.8)
            axes.set_axisbelow(True)

    def plot_status_distribution(self, _figure, axes):
        """설비 상태(정상/불량) 건수를 막대로 보여준다."""
        counts = self.dataframe["Machine failure"].value_counts().reindex([0, 1]).fillna(0)
        bars = axes.bar(
            ["정상", "불량"], counts.values, color=[STATUS_GOOD, STATUS_CRITICAL], width=0.55
        )
        total = counts.sum()
        for bar, count in zip(bars, counts.values):
            percent = (count / total * 100) if total else 0
            axes.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{int(count):,}건\n({percent:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=7,
            )
        axes.set_ylim(0, counts.max() * 1.3 if counts.max() else 1)
        self._style_axes(axes)

    def plot_type_distribution(self, _figure, axes):
        """품질 등급(Type)별 건수를 보여준다. 등급 자체는 상태가 아니므로 단일 색만 쓴다."""
        counts = self.dataframe["Type"].value_counts().reindex(["L", "M", "H"]).fillna(0)
        bars = axes.bar(counts.index, counts.values, color=SEQUENTIAL_BLUE, width=0.55)
        for bar, count in zip(bars, counts.values):
            axes.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{int(count):,}",
                ha="center",
                va="bottom",
                fontsize=7,
            )
        axes.set_ylim(0, counts.max() * 1.2 if counts.max() else 1)
        self._style_axes(axes)

    def plot_failure_mode_counts(self, _figure, axes):
        """세부 고장 모드(TWF/HDF/PWF/OSF/RNF)별 발생 건수를 보여준다. 전부 불량 원인이므로 위험 색을 쓴다."""
        counts = self.dataframe[list(FAILURE_MODE_COLUMNS)].sum()
        bars = axes.bar(FAILURE_MODE_LABELS, counts.values, color=STATUS_CRITICAL, width=0.55)
        for bar, count in zip(bars, counts.values):
            axes.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{int(count)}",
                ha="center",
                va="bottom",
                fontsize=7,
            )
        axes.set_ylim(0, counts.max() * 1.3 if counts.max() else 1)
        axes.tick_params(axis="x", labelsize=6)
        self._style_axes(axes)

    def plot_failure_rate_by_type(self, _figure, axes):
        """품질 등급별 불량률(%)을 보여준다. '불량' 지표이므로 위험 색(빨강)을 쓴다."""
        rate = (
            self.dataframe.groupby("Type")["Machine failure"]
            .mean()
            .reindex(["L", "M", "H"])
            .fillna(0)
            * 100
        )
        bars = axes.bar(rate.index, rate.values, color=STATUS_CRITICAL, width=0.55)
        for bar, value in zip(bars, rate.values):
            axes.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.2f}%",
                ha="center",
                va="bottom",
                fontsize=7,
            )
        axes.set_ylim(0, rate.max() * 1.3 if rate.max() else 1)
        axes.set_ylabel("불량률(%)", fontsize=7)
        self._style_axes(axes)

    def plot_corr(self, figure, axes):
        """수치형 변수 간 상관관계. -1~1 범위이므로 중립 회색을 지나는 발산형 컬러맵을 쓴다."""
        correlation = self.dataframe[list(CORRELATION_COLUMNS)].corr().values

        image = axes.imshow(correlation, cmap=DIVERGING_CMAP, vmin=-1, vmax=1)
        axes.set_xticks(range(len(CORRELATION_LABELS)))
        axes.set_xticklabels(CORRELATION_LABELS, fontsize=6, rotation=45, ha="right")
        axes.set_yticks(range(len(CORRELATION_LABELS)))
        axes.set_yticklabels(CORRELATION_LABELS, fontsize=6)
        for row in range(len(CORRELATION_LABELS)):
            for col in range(len(CORRELATION_LABELS)):
                value = correlation[row, col]
                axes.text(
                    col,
                    row,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=6,
                    color="#ffffff" if abs(value) >= 0.6 else "#0b0b0b",
                )
        figure.colorbar(image, ax=axes, fraction=0.046, pad=0.04)

    def plot_dist(self, _figure, axes, column, x_label):
        """정상/불량 상태별 분포를 겹쳐서 비교하는 히스토그램."""
        normal = self.dataframe.loc[self.dataframe["Machine failure"] == 0, column]
        failure = self.dataframe.loc[self.dataframe["Machine failure"] == 1, column]
        axes.hist(normal, bins=25, color=STATUS_GOOD, alpha=0.55, density=True, label="정상")
        axes.hist(failure, bins=25, color=STATUS_CRITICAL, alpha=0.65, density=True, label="불량")
        axes.set_xlabel(x_label, fontsize=7)
        axes.legend(fontsize=7, frameon=False)
        self._style_axes(axes)

    def plot_scatter(self, _figure, axes, x_column, y_column, x_label, y_label):
        """정상/불량 상태별 산점도. 불량 포인트가 도드라지도록 정상은 옅게, 불량은 진하게 그린다."""
        normal = self.dataframe[self.dataframe["Machine failure"] == 0]
        failure = self.dataframe[self.dataframe["Machine failure"] == 1]
        axes.scatter(
            normal[x_column], normal[y_column], s=6, color=STATUS_GOOD, alpha=0.25, label="정상"
        )
        axes.scatter(
            failure[x_column],
            failure[y_column],
            s=8,
            color=STATUS_CRITICAL,
            alpha=0.75,
            label="불량",
        )
        axes.set_xlabel(x_label, fontsize=7)
        axes.set_ylabel(y_label, fontsize=7)
        axes.legend(fontsize=7, frameon=False, markerscale=2)
        self._style_axes(axes)

    def plot_box(self, _figure, axes, column, y_label):
        """정상/불량 상태별 분포를 박스플롯으로 비교한다."""
        normal = self.dataframe.loc[self.dataframe["Machine failure"] == 0, column]
        failure = self.dataframe.loc[self.dataframe["Machine failure"] == 1, column]
        box = axes.boxplot(
            [normal, failure], tick_labels=["정상", "불량"], patch_artist=True, widths=0.5
        )
        for patch, color in zip(box["boxes"], [STATUS_GOOD, STATUS_CRITICAL]):
            patch.set_facecolor(color)
            patch.set_alpha(0.55)
        for median_line in box["medians"]:
            median_line.set_color("#0b0b0b")
        axes.set_ylabel(y_label, fontsize=7)
        self._style_axes(axes)
