import os
from datetime import time
from typing import List

import pandas as pd
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from src.mod.O_prompt import SYSTEM, USER
from pydantic import BaseModel, Field

load_dotenv()
USER_AGENT = os.environ.get("USER_AGENT")
api_key = os.environ.get("GOOGLE_API")


class SpeechAgenda(BaseModel):
    title: str = Field(description="演講主題")
    start_time: str = Field(description="開始時間")
    end_time: str = Field(description="結束時間")
    speaker_title: str = Field(description="講者職稱與單位", default="無")
    speaker_name: str = Field(description="講者姓名", default="無")
    script: str = Field(description="司儀稿內容")


class AgendaSchedule(BaseModel):
    event_name: str = Field(description="活動名稱")
    agendas: List[SpeechAgenda] = Field(description="議程清單")


def load_content(source: str, source_type: str):
    """
    根據 source_type 讀取內容
    source_type: 'url' or 'file'
    """
    try:
        if source_type == 'url':
            loader = WebBaseLoader(source)
        elif source_type == 'file':
            ext = os.path.splitext(source)[1].lower()
            if ext == '.pdf':
                loader = PyPDFLoader(source)
            elif ext == '.csv':
                loader = CSVLoader(source, encoding='utf-8')
            elif ext == '.xlsx':
                loader = UnstructuredExcelLoader(source)
            elif ext == '.docx':
                loader = Docx2txtLoader(source)
            elif ext == '.md':
                loader = UnstructuredMarkdownLoader(source)
            else:
                # 預設嘗試用文字讀取
                loader = TextLoader(source, encoding='utf-8')
        else:
            return "不支援的輸入類型"

        docs = loader.load()
        # 合併所有頁面的內容
        content = "\n\n".join([doc.page_content for doc in docs])
        return content

    except Exception as e:
        return f"讀取內容時發生錯誤: {str(e)}"


def connect_llm_model(model_name: str, api_key=api_key):
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key
    )


def create_prompt_template():
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM),
        ("human", USER)
    ])


def create_prompt_data(content):
    json_parser = JsonOutputParser()

    pydantic_parser = PydanticOutputParser(
        pydantic_object=AgendaSchedule
    )
    pydantic_prompt = pydantic_parser.get_format_instructions()

    return json_parser, {
        "web_content": content,
        "pydantic_parser": pydantic_prompt
    }


def get_tokens_info(ai_message):
    if hasattr(ai_message, 'usage_metadata'):
        tokens = ai_message.usage_metadata
        return tokens['input_tokens'], tokens['output_tokens']


def transform_to_df(response, key="agendas"):
    # 如果 response 是 AgendaSchedule 對象 (Pydantic model)
    if isinstance(response, AgendaSchedule):
        data_list = [item.dict() for item in response.agendas]
        return pd.DataFrame(data_list)

    # 如果 response 是 dict
    if isinstance(response, dict):
        if key in response:
            return pd.DataFrame(response[key])
        return pd.DataFrame([response])  # 嘗試轉為單行

    return pd.DataFrame()
