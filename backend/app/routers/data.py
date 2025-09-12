from fastapi import APIRouter, UploadFile, HTTPException
import mlflow
from app.services import mlflow_svc, state

router = APIRouter(prefix="/api/project", tags=["data"])


@router.post("/{pid}/upload")
async def upload_data(pid: str, file: UploadFile):
    """업로드된 CSV 파일을 읽어 MLflow에 기록하고, 인메모리 상태에 저장합니다."""
    if not state.has_project(pid):
        raise HTTPException(status_code=404, detail="Project not found")

    with mlflow.start_run(experiment_id=pid, run_name="upload_file") as run:
        try:
            df = mlflow_svc.log_uploaded_file_as_artifact(file, run.info.run_id)
            state.set_dataframe_initial(pid, df)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File processing failed: {e}")

        return {
            "name": file.filename,
            "run_id": run.info.run_id,
            "message": "Data uploaded successfully",
        }


@router.get("/{pid}/data")
def list_datasets(pid: str):
    """프로젝트에 포함된 모든 데이터셋 아티팩트 목록을 반환합니다."""
    if not state.has_project(pid):
        raise HTTPException(status_code=404, detail="Project not found")

    datasets = mlflow_svc.list_project_datasets(pid)
    return {"datasets": datasets}