from typing import Dict, Any, Optional
import pandas as pd

# --- 인메모리 상태 저장소 ---
# key: project_id, value: 프로젝트 관련 상태 정보
# 단일 사용자 및 개발/데모용으로, 서버 재시작 시 모든 상태가 초기화됩니다.
PROJECTS: Dict[str, Dict[str, Any]] = {}


def create_project(project_id: str) -> None:
    """새로운 프로젝트를 위한 상태 공간을 초기화합니다."""
    if project_id in PROJECTS:
        return  # 이미 존재하면 아무것도 하지 않음
    PROJECTS[project_id] = {
        "current_df": None,  # 현재 처리 중인 데이터프레임
        "original_df": None,  # 원본 데이터프레임 (불변)
        "active_dataset": None,  # 현재 활성화된 데이터셋의 MLflow 아티팩트 경로
    }


def has_project(project_id: str) -> bool:
    """주어진 ID의 프로젝트가 존재하는지 확인합니다."""
    return project_id in PROJECTS


def set_dataframe_initial(project_id: str, df: pd.DataFrame) -> None:
    """프로젝트의 초기 데이터프레임을 설정합니다."""
    if not has_project(project_id):
        create_project(project_id)

    p = PROJECTS[project_id]
    if p.get("original_df") is not None:
        # 실무에서는 덮어쓰기 또는 버전 관리 정책을 고려할 수 있습니다.
        raise ValueError("Initial dataset already exists for this project.")

    p["current_df"] = df
    p["original_df"] = df.copy()  # 원본 보존을 위해 복사


def set_active_dataset(project_id: str, artifact_rel_path: str) -> None:
    """현재 활성화된 데이터셋의 아티팩트 경로를 설정합니다."""
    if has_project(project_id):
        PROJECTS[project_id]["active_dataset"] = artifact_rel_path


def get_active_dataset(project_id: str) -> Optional[str]:
    """활성화된 데이터셋의 아티팩트 경로를 가져옵니다."""
    if has_project(project_id):
        return PROJECTS[project_id].get("active_dataset")
    return None


def get_current_df(project_id: str) -> Optional[pd.DataFrame]:
    """현재 사용 중인 데이터프레임을 가져옵니다."""
    if has_project(project_id):
        return PROJECTS[project_id].get("current_df")
    return None


def set_current_df(project_id: str, df: pd.DataFrame) -> None:
    """현재 데이터프레임을 업데이트합니다."""
    if has_project(project_id):
        PROJECTS[project_id]["current_df"] = df
