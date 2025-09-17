from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.memory import ConversationBufferWindowMemory

import pandas as pd
from dotenv import load_dotenv
import os

from src.langchain_tools import (
    python_executor,
    list_dataframes,
    set_active_dataframe,
    delete_dataframe,
    state,
)

load_dotenv()


def create_project_agent_executor(chat_history: list = None):
    """
    프로젝트별로 독립된 메모리를 가진 에이전트 실행기를 생성하는 함수.
    """
    # 1. LLM 초기화
    llm = ChatGoogleGenerativeAI(model="gemini-pro")

    # 2. ReAct 프롬프트 템플릿 가져오기
    prompt = hub.pull("hwchase17/react-chat")

    # 3. 메모리 객체 생성
    memory = ConversationBufferWindowMemory(
        k=10, memory_key="chat_history", return_messages=True
    )

    # 만약 불러온 프로젝트의 채팅 기록이 있다면, 메모리에 미리 채워넣습니다.
    if chat_history:
        for message in chat_history:
            if message["sender"] == "user":
                memory.chat_memory.add_user_message(message["content"])
            else:
                memory.chat_memory.add_ai_message(message["content"]["final_answer"])
    tools = [
        python_executor,
        list_dataframes,
        set_active_dataframe,
        delete_dataframe,
    ]

    # 4. 에이전트 생성
    agent = create_react_agent(llm, tools, prompt)

    # 5. 에이전트 실행기에 'memory'를 연결
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
    )

    return agent_executor


agent_executor = create_project_agent_executor()
