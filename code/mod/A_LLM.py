import os
from datetime import time
from typing import List

import pandas as pd
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from mod.O_prompt import SYSTEM, USER
from pydantic import BaseModel, Field

load_dotenv()
USER_AGENT = os.environ.get("USER_AGENT")
api_key = os.environ.get("GOOGLE_API")


class SpeechAgenda(BaseModel):
    title: str = Field(description="演講主題")
    start_time: time = Field(description="開始時間")
    end_time: time = Field(description="結束時間")
    speaker_title: str = Field(description="講者職稱與單位", default="無")
    speaker_name: str = Field(description="講者姓名", default="無")
    script: str = Field(description="司儀稿內容")


class AgendaSchedule(BaseModel):
    event_name: str = Field(description="活動名稱")
    agendas: List[SpeechAgenda] = Field(description="議程清單")


def load_web_info(url: str):
    loader = WebBaseLoader(url)
    docs = loader.load()
    web_content = docs[0].page_content

    return web_content


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


def create_prompt_data(web_content):
    json_parser = JsonOutputParser()

    pydantic_parser = PydanticOutputParser(
        pydantic_object=AgendaSchedule
    )
    pydantic_prompt = pydantic_parser.get_format_instructions()

    return json_parser, {
        "web_content": web_content,
        "pydantic_parser": pydantic_prompt
    }


def get_tokens_info(ai_message):
    if hasattr(ai_message, 'usage_metadata'):
        tokens = ai_message.usage_metadata
        return tokens['input_tokens'], tokens['output_tokens']


def transform_to_df(response, key):
    return pd.DataFrame(response[key])
