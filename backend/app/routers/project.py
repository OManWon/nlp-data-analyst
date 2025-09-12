from fastapi import APIRouter, HTTPException
import mlflow
import shutil
from app.services import state

router = APIRouter(prefix="/api/project", tags=["project"])


@router.post("/new")
def new_project(name: str):
    """새 프로젝트(MLflow Experiment)를 생성하고, 인메모리 상태를 초기화합니다."""
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required")

    try:
        experiment = mlflow.create_experiment(name)
        state.create_project(experiment)
        return {"experiment_id": experiment}
    except Exception as e:
        # MLflow에서 이미 존재하는 Experiment를 생성하려고 할 때 발생하는 오류 처리
        raise HTTPException(status_code=409, detail=f"Project '{name}' already exists.")


@router.get("/list")
def list_projects():
    """모든 프로젝트(MLflow Experiment) 목록을 반환합니다."""
    experiments = mlflow.search_experiments()
    return [
        {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "artifact_location": experiment.artifact_location,
        }
        for experiment in experiments
    ]


@router.delete("/delete")
def delete_project(name: str):
    """프로젝트(MLflow Experiment)를 삭제합니다."""
    experiment = mlflow.get_experiment_by_name(name)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # MLflow Experiment 삭제
    mlflow.delete_experiment(experiment.experiment_id)

    # .trash 디렉토리 정리 (shutil을 사용하여 안전하게 삭제)
    trash_path = f"mlruns/.trash/{experiment.experiment_id}"
    try:
        shutil.rmtree(trash_path)
    except FileNotFoundError:
        pass  # .trash 디렉토리가 없으면 무시
    except Exception as e:
        # 로깅 또는 적절한 오류 처리를 추가할 수 있습니다.
        print(f"Error deleting trash directory {trash_path}: {e}")

    return {"message": "Project deleted successfully"}
