
import os
import tempfile
import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
from fastapi import UploadFile
import json

# MLflow 설정
MLRUNS_DIR = os.getenv("MLRUNS_DIR", "./mlruns")
mlflow.set_tracking_uri(f"file://{os.path.abspath(MLRUNS_DIR)}")
_client = MlflowClient(tracking_uri=mlflow.get_tracking_uri())


def log_plot_file(path: str, run_id: str, rel_dir: str = "plots") -> None:
    """matplotlib으로 생성된 플롯 파일을 MLflow에 아티팩트로 기록합니다."""
    with mlflow.start_run(run_id=run_id, nested=True):
        mlflow.log_artifact(path, artifact_path=rel_dir)


def log_uploaded_file_as_artifact(file: UploadFile, run_id: str):
    """업로드된 파일을 읽어 데이터프레임으로 변환 후 MLflow 아티팩트로 저장합니다."""
    with mlflow.start_run(run_id=run_id, nested=True):
        with tempfile.TemporaryDirectory() as td:
            fpath = os.path.join(td, file.filename)
            df = pd.read_csv(file.file)
            df.to_csv(fpath, index=False)
            mlflow.log_artifact(fpath, artifact_path="data")
            return df


def log_dataframe_as_artifact(
    df: pd.DataFrame, filename: str, run_id: str, rel_dir: str = "data"
) -> str:
    """데이터프레임을 CSV 파일로 저장하고 MLflow 아티팩트로 기록합니다."""
    with mlflow.start_run(run_id=run_id, nested=True):
        with tempfile.TemporaryDirectory() as td:
            fpath = os.path.join(td, filename)
            df.to_csv(fpath, index=False)
            mlflow.log_artifact(fpath, artifact_path=rel_dir)
            return f"{rel_dir}/{filename}"


def log_chat_history(run_id: str, chat_history: list) -> None:
    """채팅 기록을 JSON 파일로 저장하여 MLflow 아티팩트로 기록합니다."""
    with mlflow.start_run(run_id=run_id, nested=True):
        with tempfile.TemporaryDirectory() as td:
            fpath = os.path.join(td, "chat_history.json")
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(chat_history, f, ensure_ascii=False, indent=2)
            mlflow.log_artifact(fpath, artifact_path="chat")


def get_latest_run_id(project_id: str) -> str | None:
    """프로젝트에서 가장 최근의 Run ID를 반환합니다."""
    runs = _client.search_runs([project_id], order_by=["start_time DESC"], max_results=1)
    return runs[0].info.run_id if runs else None


def load_chat_history(run_id: str) -> list:
    """MLflow Run에서 채팅 기록 아티팩트를 불러옵니다."""
    try:
        # 아티팩트 경로 다운로드
        local_path = _client.download_artifacts(run_id, "chat/chat_history.json")
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # 파일이 없거나 오류 발생 시 빈 리스트 반환
        return []


def list_run_artifacts(run_id: str, path: str = "") -> list:
    """특정 MLflow Run에 기록된 아티팩트 목록을 재귀적으로 조회합니다."""
    infos = _client.list_artifacts(run_id, path)
    out = []
    for info in infos:
        item = {
            "path": info.path,
            "is_dir": info.is_dir,
            "file_size": getattr(info, "file_size", None),
        }
        out.append(item)
        if info.is_dir:
            out.extend(list_run_artifacts(run_id, info.path))
    return out


def list_project_datasets(pid: str) -> list:
    """프로젝트(Experiment) 내 모든 데이터셋(.csv) 아티팩트를 조회합니다."""
    datasets = []
    for r in _client.search_runs([pid]):
        run_id = r.info.run_id
        try:
            artifacts = list_run_artifacts(run_id, "data")
        except Exception:
            artifacts = []

        for a in artifacts:
            if not a["is_dir"] and a["path"].lower().endswith(".csv"):
                datasets.append({"run_id": run_id, "path": a["path"]})
    return datasets
