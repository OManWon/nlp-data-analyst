import os
import time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sklearn
import mlflow
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_experimental.tools.python.tool import PythonAstREPLTool
from langchain_google_genai import ChatGoogleGenerativeAI

from app.services import state, mlflow_svc

load_dotenv()

# 기본 실행 네임스페이스
safe_ns = {
    "pd": pd,
    "sns": sns,
    "plt": plt,
    "mlflow": mlflow,
    "sklearn": sklearn,
}

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    max_output_tokens=2048,
)

# 도구는 요청 처리 중 동적으로 네임스페이스가 주입됨
python_tool = PythonAstREPLTool(locals=safe_ns)

AGENT_PROMPT = """
- You are a data analysis expert.
- The user will ask questions about a CSV dataset.
- To access the dataframe, you MUST use `df = get_current_df()`.
- Any modifications to the dataframe should be assigned back to the `df` variable, for example: `df = df.dropna()`.
- Do not print raw data rows. Use schema or summary statistics instead.
- After plotting, you MUST call `plt.savefig('/tmp/plot.png')` and then `plt.close('all')`.
- Respond with a plan and the executable python code.
"""

agent = create_react_agent(model=llm, tools=[python_tool], prompt=AGENT_PROMPT)


def _invoke_agent(user_query: str, chat_history: list) -> dict:
    """에이전트를 호출하고 전체 응답을 반환합니다."""
    history_messages = []
    for msg in chat_history:
        if msg["role"] == "user":
            history_messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("plan"):
            history_messages.append(AIMessage(content=msg["plan"]))

    return agent.invoke(
        {
            "messages": [HumanMessage(content=user_query)],
            "chat_history": history_messages,
        }
    )


def _log_run_details(
    user_query: str, plan: str, code: str, df: pd.DataFrame | None
) -> None:
    mlflow.log_param("user_query", user_query)
    mlflow.log_param("agent_plan", plan)
    mlflow.log_param("executed_code", code)
    rows, cols = (df.shape[0], df.shape[1]) if df is not None else (0, 0)
    mlflow.log_metrics({"rows": rows, "cols": cols})


def run_agent(pid: str, user_query: str, chat_history: list) -> dict:
    with mlflow.start_run(experiment_id=pid, run_name="chat") as run:
        run_id = run.info.run_id

        # 1. 에이전트 실행 전 상태 저장
        df_before = state.get_current_df(pid)
        df_before_copy = df_before.copy() if df_before is not None else None

        # 2. 에이전트 호출을 위한 동적 컨텍스트 설정
        def get_current_df_for_agent():
            return state.get_current_df(pid)

        # 현재 요청에 대한 네임스페이스 생성
        locals_for_tool = {**safe_ns, "get_current_df": get_current_df_for_agent}
        if df_before is not None:
            locals_for_tool["df"] = df_before

        original_locals = python_tool.locals
        python_tool.locals = locals_for_tool

        try:
            # 3. 에이전트 호출
            agent_resp = _invoke_agent(user_query, chat_history)

        finally:
            # 4. 컨텍스트 원상 복구 (중요)
            python_tool.locals = original_locals

        # 5. 에이전트 실행 결과 파싱
        plan = agent_resp.get("messages", [{}])[-1].content
        code, observation, error = "", "", ""
        if agent_resp.get("intermediate_steps"):
            action, observation_str = agent_resp["intermediate_steps"][-1]
            code = action.tool_input
            if "Traceback" in observation_str:
                error = observation_str
            else:
                observation = observation_str

        # 6. 상태 업데이트 (데이터프레임 변경 시)
        # 에이전트 실행 후 업데이트된 네임스페이스에서 df를 가져옴
        if "df" in locals_for_tool and isinstance(locals_for_tool["df"], pd.DataFrame):
            new_df = locals_for_tool["df"]
            state.set_current_df(pid, new_df)

        df_after = state.get_current_df(pid)

        # 7. 아티팩트 및 MLflow Run 상세 정보 로깅
        artifacts, active_dataset = [], None
        df_changed = not (
            df_before_copy.equals(df_after)
            if df_before_copy is not None and df_after is not None
            else df_before_copy is df_after
        )

        if df_changed and df_after is not None:
            filename = f"df_{int(time.time())}.csv"
            rel_path = mlflow_svc.log_dataframe_as_artifact(
                df=df_after, filename=filename, run_id=run_id
            )
            state.set_active_dataset(pid, rel_path)
            active_dataset = rel_path
            artifacts.append({"type": "dataset", "path": rel_path})

        plot_path = "/tmp/plot.png"
        if os.path.exists(plot_path):
            mlflow_svc.log_plot_file(plot_path, run_id=run_id)
            artifacts.append({"type": "plot", "path": "plots/plot.png"})
            try:
                os.remove(plot_path)
            except OSError as e:
                print(f"Error removing plot file: {e}")

        _log_run_details(user_query, plan, code, df_after)

        # 8. 채팅 기록 업데이트 및 저장
        user_message = {"role": "user", "content": user_query}
        assistant_message = {
            "role": "assistant",
            "run_id": run_id,
            "plan": plan,
            "code": code,
            "artifacts": artifacts,
            "active_dataset": active_dataset,
            "stdout": observation,
            "stderr": "",  # PythonAstREPLTool은 stderr을 별도로 캡처하지 않음
            "error": error,
        }
        updated_history = chat_history + [user_message, assistant_message]
        mlflow_svc.log_chat_history(run_id, updated_history)

        return assistant_message
