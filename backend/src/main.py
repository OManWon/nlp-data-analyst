from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import json
import pandas as pd

from state_manager import ProjectStateManager
from langchain_tools import (
    list_dataframes,
    set_active_dataframe,
    delete_dataframe,
    state,
)
from models import (
    Node,
    Edge,
    DataFramePreview,
    AgentThought,
    AgentResponse,
    ProjectStateResponse,
)

from langchain_agent_runner import agent_executor

app = FastAPI()

origins = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/project/state", response_model=ProjectStateResponse)
def get_project_state():
    """
    현재 프로젝트의 상태(모든 데이터프레임과 그 관계)를
    시각화에 적합한 JSON 형식으로 반환합니다.
    """
    nodes = []
    edges = []

    for df_id, info in state.dataframes.items():
        # 노드 리스트에 DF 정보 추가
        nodes.append(
            Node(id=df_id, label=f"{info.name} ({info.shape[0]}x{info.shape[1]})")
        )

        # 부모가 있는 경우, 엣지(연결선) 리스트에 관계 정보 추가
        if info.parent_id:
            edges.append(
                Edge(source=info.parent_id, target=df_id, label=info.operation)
            )

    return ProjectStateResponse(
        nodes=nodes, edges=edges, active_node_id=state.active_df_id
    )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    사용자가 업로드한 CSV 파일을 읽어
    새로운 데이터프레임으로 프로젝트에 등록합니다.
    """
    try:
        # 업로드된 파일의 이름을 가져옵니다.
        filename = file.filename
        print(f"파일 수신: {filename}")

        # 파일을 Pandas 데이터프레임으로 직접 읽어들입니다.
        # file.file은 임시 파일 객체입니다.
        df = pd.read_csv(file.file)

        # 새로운 데이터프레임을 상태 관리자에 등록합니다.
        state.register_df(
            name=f"{filename} (원본)",
            variable_name="df_initial",  # 초기 변수명은 통일
            df_object=df,
            operation="파일 업로드",
        )
        return {"message": f"'{filename}' 파일이 성공적으로 업로드 및 등록되었습니다."}
    except Exception as e:
        # 텍스트 파일이 아니거나 형식이 잘못된 경우 등 예외 처리
        return {"error": f"파일 처리 중 오류 발생: {e}"}


@app.post("/api/agent/invoke")
async def invoke_agent(payload: dict):
    """
    사용자의 입력을 받아 랭체인 에이전트를 실행하고,
    '생각의 흐름'을 포함한 상세 결과를 반환합니다.
    """
    user_input = payload.get("input")
    if not user_input:
        return {"error": "Input is required"}

    # 'return_intermediate_steps=True'를 추가하여 중간 과정을 받아옵니다.
    response = agent_executor.invoke(
        {"input": user_input}, return_intermediate_steps=True
    )

    thoughts = []
    if "intermediate_steps" in response:
        for step in response["intermediate_steps"]:
            action = step[0]  # AgentAction
            thoughts.append(
                AgentThought(
                    tool=action.tool, tool_input=str(action.tool_input), log=action.log
                )
            )

    return AgentResponse(thoughts=thoughts, final_answer=response.get("output", ""))


@app.get("/api/project/plots")
async def get_project_plots():
    """현재 프로젝트에 저장된 모든 플롯의 목록을 반환합니다."""
    return state.plots


@app.get("/api/dataframe/{df_id}/preview", response_model=DataFramePreview)
async def get_dataframe_preview(df_id: str):
    """
    주어진 df_id에 해당하는 데이터프레임의 상위 5개 행(head)을
    JSON 형식으로 반환합니다.
    """
    if df_id in state.dataframes:
        df_obj = state.dataframes[df_id].df_object
        preview_json = df_obj.head().to_json(orient="split", index=False)
        return json.loads(preview_json)
    else:
        return {"error": "DataFrame not found"}


if __name__ == "__main__":
    import uvicorn
    import pandas as pd

    df_initial = pd.DataFrame(
        {"지역": ["서울", "부산", "서울"], "매출": [100, 80, 120]}
    )
    state.register_df("원본 데이터", "df_initial", df_initial)

    uvicorn.run(app, host="127.0.0.1", port=8000)
