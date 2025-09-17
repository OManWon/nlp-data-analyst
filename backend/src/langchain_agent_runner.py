from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
import pandas as pd
from dotenv import load_dotenv
import os

from langchain_tools import (
    python_executor,
    list_dataframes,
    set_active_dataframe,
    delete_dataframe,
    state,
)

load_dotenv()

# --- LLM 초기화 ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")
)

# --- 도구 리스트 정의 ---
tools = [python_executor, list_dataframes, set_active_dataframe, delete_dataframe]

# --- ReAct 프롬프트 템플릿 가져오기 ---
prompt = hub.pull("hwchase17/react")

# --- 에이전트 생성 ---
agent = create_react_agent(llm, tools, prompt)

# --- 실행기 생성 ---
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)