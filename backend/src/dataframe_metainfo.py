import pandas as pd
from datetime import datetime


class DataFrameMetaInfo:
    """
    각 데이터 프레임의 메타 정보를 저장하는 클래스
    """

    def __init__(
        self,
        df_id: str,
        name: str,
        variable_name: str,
        df_object: pd.DataFrame,
        parent_id: str = None,
        operation: str = "N/A",
    ):
        self.id: str = df_id  # 고유 ID
        self.name: str = name  # LLM이 지어준 이름 (예: after_merging.csv)
        self.variable_name: str = variable_name  # 실제 코드에서 쓰이는 변수명 (예: df)
        self.df_object: pd.DataFrame = df_object  # 메모리에 있는 실제 데이터프레임 객체

        self.parent_id: str | None = parent_id  # 부모 데이터프레임의 ID
        self.operation: str = operation

        self.timestamp: datetime = datetime.now()  # 생성 시간
        self.shape = df_object.shape  # 데이터의 형태 (행, 열)

    def __repr__(self):
        return f"[{self.id}] {self.name} ({self.shape[0]} X {self.shape[1]}) - Parent: {self.parent_id}"
