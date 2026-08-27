"""노트북을 .venv 커널로 확실하게 실행하는 헬퍼.

`jupyter nbconvert --execute`는 이 개발 환경(PowerShell 프로필의 `conda init` 훅이 매 새
셸마다 CONDA_PREFIX/VIRTUAL_ENV를 주입함)에서 커널 탐색 시 실제로 호출한 인터프리터가 아니라
Anaconda 베이스나 예전 venv로 슬쩍 새는 문제가 있다 (docs/troubleshooting.md 참고). 게다가
`--ExecutePreprocessor.kernel_name=...` CLI 플래그로 강제해도 이 환경에서는 무시된다(원인 불명,
재현 확인됨). 이 스크립트는 nbclient를 직접 호출해 커널 이름을 코드로 못박아서 그 문제를 완전히
우회한다.

사용법 (반드시 .venv의 python으로 실행할 것 — 다른 파이썬으로 실행하면 아래 KERNEL_NAME이
가리키는 커널 자체가 없다는 에러가 난다):
    ./.venv/Scripts/python scripts/run_notebook.py src/EDA1.ipynb [src/model_3.ipynb ...]

최초 1회, 이 커널이 없다면 먼저 등록해야 한다:
    ./.venv/Scripts/python -m ipykernel install --user --name cnc-venv --display-name "Python (.venv - CNC project)"
"""

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

KERNEL_NAME = "cnc-venv"


def run_notebook(notebook_path: Path) -> None:
    notebook_path = notebook_path.resolve()
    nb = nbformat.read(notebook_path, as_version=4)
    # nbconvert의 기본 동작과 동일하게, 노트북이 있는 폴더를 작업 디렉터리로 실행한다
    # (노트북 안의 pd.read_csv("ai4i2020.csv")/savefig("../images/...")가 이걸 전제로 함).
    client = NotebookClient(
        nb,
        kernel_name=KERNEL_NAME,
        resources={"metadata": {"path": str(notebook_path.parent)}},
        timeout=600,
    )
    print(f"[run_notebook] {notebook_path.name} 실행 중 (kernel={KERNEL_NAME})...")
    client.execute()
    nbformat.write(nb, notebook_path)
    print(f"[run_notebook] 완료: {notebook_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python scripts/run_notebook.py <notebook.ipynb> [<notebook2.ipynb> ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        run_notebook(Path(arg))
