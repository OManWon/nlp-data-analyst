import pandas as pd
import uuid

from .dataframe_metainfo import DataFrameMetaInfo


class ProjectStateManager:
    """
    프로젝트의 모든 데이터 프레임 상태를 관리하는 총괄 클래스
    """

    def __init__(self):
        self.dataframes: dict[str, DataFrameMetaInfo] = (
            {}
        )  # 모든 DF 정보를 여기에 저장 {ID: DataFrameMetaInfo}
        self.active_df_id: str | None = None  # 현재 활성화 된 DF의 ID
        self._df_counter = 0

    def _generate_id(self):
        self._df_counter += 1
        return f"df_{self._df_counter:03d}"

    def register_df(
        self,
        name: str,
        variable_name: str,
        df_object: pd.DataFrame,
        parent_id: str = None,
        operation: str = "N/A",
    ) -> DataFrameMetaInfo:
        """
        새로운 데이터 프레임을 시스템에 등록.
        LLM 에이전트는 DF를 생성할 때 이 함수를 호출
        """
        new_id = self._generate_id()
        metainfo = DataFrameMetaInfo(
            df_id=new_id,
            name=name,
            variable_name=variable_name,
            df_object=df_object,
            parent_id=parent_id,
            operation=operation,
        )
        self.dataframes[new_id] = metainfo
        self.active_df_id = new_id
        print(f"새 데이터 프레임 등록: {metainfo}")
        return metainfo

    def list_dfs_for_display(self):
        """
        UI에 보여줄 텍스트 목록
        """
        display_list = []
        for df_id, info in self.dataframes.items():
            prefix = "=>  " if df_id == self.active_df_id else "    "
            display_list.append(
                f"{prefix}[{info.id}] {info.name} ({info.shape[0]} X {info.shape[1]})"
            )
        return display_list

    def set_active_df(self, df_id):
        """
        지정된 ID의 데이터 프레임을 활성화함.
        """
        if df_id in self.dataframes:
            self.active_df_id = df_id
            print(f"활성 데이터 프레임 변경: [{df_id}]")
            return True
        else:
            print(f"Error: 존재하는 ID입니다. ({df_id})")
            return False

    def delete_df(self, df_id):
        """
        지정된 ID의 데이터 프레임을 삭제함.
        """
        if df_id not in self.dataframes:
            print(f"❌ 오류: 존재하지 않는 ID입니다 ({df_id}).")
            return False

        deleted_info = self.dataframes.pop(df_id)
        print(f"🗑️ 데이터 프레임 삭제: [{deleted_info.id}] {deleted_info.name}")

        # 만약 삭제한 DF가 활성 상태였다면, 다른 DF를 활성화해야 합니다.
        if self.active_df_id == df_id:
            # 우선순위: 1. 부모 DF, 2. 남아있는 DF 중 가장 최근 것
            new_active_id = deleted_info.parent_id
            if new_active_id not in self.dataframes:
                # 남아있는 df가 있다면 가장 마지막 것을 활성화
                if self.dataframes:
                    new_active_id = list(self.dataframes.keys())[-1]
                else:  # 전부 삭제되었다면 None
                    new_active_id = None

            self.active_df_id = new_active_id
            if new_active_id:
                print(f"➡️  새로운 활성 데이터 프레임: [{new_active_id}]")

        return True

    def get_active_df_object(self):
        """
        현재 활성화된 실제 데이터프레임 객체를 반환
        LLM 에이전트가 코드를 생성할 때 이 함수 사용.
        """
        if self.active_df_id:
            return self.dataframes[self.active_df_id].df_object
        return None

    def get_active_df_info(self):
        """
        현재 활성화된 데이터프레임의 정보를 반환
        """
        if self.active_df_id:
            return self.dataframes[self.active_df_id]
        return None
