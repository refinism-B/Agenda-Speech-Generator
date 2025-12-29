import os

from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from mod.O_prompt import SYSTEM, USER
import pandas as pd


load_dotenv()
USER_AGENT = os.environ.get("USER_AGENT")
api_key = os.environ.get("GOOGLE_API")


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
    json_prompt = json_parser.get_format_instructions()

    return json_parser, {
        "web_content": web_content,
        "json_parser": json_prompt
    }


def get_tokens_info(ai_message):
    if hasattr(ai_message, 'usage_metadata'):
        tokens = ai_message.usage_metadata
        return tokens['input_tokens'], tokens['output_tokens']


def transform_to_df(response):
    data = {
        "時間": list(response.keys()),
        "講稿": list(response.values())
    }

    return pd.DataFrame(data)
