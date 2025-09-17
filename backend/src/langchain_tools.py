import pandas as pd
import io, contextlib
import base64
from matplotlib import pyplot as plt
import seaborn as sns
from langchain.tools import tool
from state_manager import ProjectStateManager

# 상태 관리 객체
state = ProjectStateManager()


# --- 데이터프레임 관리 도구들 ---
@tool
def list_dataframes() -> str:
    """현재 프로젝트에 있는 모든 데이터 프레임의 목록과 상태를 문자열로 반환합니다."""
    return "\n".join(state.list_dfs_for_display())


@tool
def set_active_dataframe(df_id: str) -> str:
    """주어진 df_id를 가진 데이터 프레임을 활성화하여 다음 작업의 기본 데이터로 설정합니다."""
    success = state.set_active_df(df_id)
    return (
        f"성공: [{df_id}]가 활성 데이터 프레임으로 설정되었습니다."
        if success
        else f"실패: [{df_id}]를 찾을 수 없습니다."
    )


@tool
def delete_dataframe(df_id: str) -> str:
    """주어진 df_id를 가진 데이터 프레임을 프로젝트에서 삭제합니다."""
    success = state.delete_df(df_id)
    return (
        f"성공: [{df_id}]를 삭제했습니다."
        if success
        else f"실패: [{df_id}]를 찾을 수 없습니다."
    )


@tool
def python_executor(code: str, new_variable_name: str = None) -> dict:
    """
    Pandas, Matplotlib, Seaborn을 사용하여 코드를 실행하기 위한 Python 실행기.
    활성화된 데이터프레임은 'df' 변수로 제공됩니다.
    새로운 데이터프레임을 만들려면 반드시 'new_df = ...' 형태로 작성하세요.
    이때, 사용자가 이해하기 쉬운 새 데이터프레임의 이름을 'new_variable_name' 파라미터로 함께 전달할 수 있습니다.
    이름을 전달하지 않으면 자동으로 이름이 생성됩니다.
    그래프를 그리려면 코드 마지막에 'plt.show()'를 반드시 호출해야 합니다.
    """
    active_df_info = state.get_active_df_info()
    if not active_df_info:
        return {
            "text_result": "오류: 활성 데이터프레임이 없습니다.",
            "image_base64": None,
        }

    # 활성 데이터를 df라는 변수로 접근하게 함.
    local_vars = {"df": active_df_info.df_object.copy(), "plt": plt, "sns": sns}
    plt.close("all")

    f = io.StringIO()
    text_output = ""
    try:
        with contextlib.redirect_stdout(f):
            exec(code, {}, local_vars)
        text_output = f.getvalue()  # 기본 성공 메시지
        print(local_vars)
    except Exception as e:
        return {"text_result": f"실행 오류: {e}", "image_base64": None}

    # 이미지 캡처 로직
    image_base64 = None
    # 이렇게 하는 이유는, 파일 시스템을 사용하지 않기 위해서.
    # 프론트엔드에서 바로 받아서 보여줄 수 있다.
    if plt.get_fignums():  # plt로 그림을 그린게 있다면
        buf = io.BytesIO()
        plt.savefig(buf, format="png")  # 버퍼에 fig를 save하고
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode(
            "utf-8"
        )  # 버퍼를 다시 읽어서 텍스트로 인코딩한다.
        plt.close("all")
        state.register_plot(image_base64, code)

    # new_df 생성 여부 확인 및 등록
    if "new_df" in local_vars and isinstance(local_vars["new_df"], pd.DataFrame):
        new_df_obj = local_vars["new_df"]
        parent_id = active_df_info.id

        final_name = (
            new_variable_name if new_variable_name else f"{parent_id}로부터 파생됨"
        )
        variable_name = new_variable_name if new_variable_name else "new_df"

        state.register_df(
            name=final_name,
            variable_name=variable_name,
            df_object=new_df_obj,
            parent_id=parent_id,
            operation=code,
        )
        text_output += f"\n새로운 데이터프레임 '{final_name}'이 생성되었습니다."

    return {"text_result": text_output, "image_base64": image_base64}
