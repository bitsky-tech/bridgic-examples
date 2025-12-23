import os
import typing as t
from pydantic import BaseModel

from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Role, Message, Response, Tool
from bridgic.core.model.protocols import Constraint, PydanticModel


async def allm_worker(
    model: str,
    messages: t.List[Message], 
    *,
    tools: t.List[Tool] = [],
    tool_choice: t.Literal["auto", "required", "none"] = "auto",
    timeout: int = 120,
    max_tokens: int = 2048,
    type: str = "chat",
    constraint: Constraint = None,
    **kwargs: t.Any
) -> Response:
    # 从环境变量读取 API 配置
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY 环境变量未设置。请设置环境变量或创建 .env 文件。"
            "参考 .env.example 文件了解如何配置。"
        )
    
    llm = OpenAILlm(
        api_base=api_base,
        api_key=api_key,
        configuration=OpenAIConfiguration(
            model=model,
            temperature=0.0,
            max_tokens=max_tokens,
            **kwargs
        ),
        timeout=timeout,
    )
    if type == "chat":
        response = await llm.achat(messages=messages)
    elif type == "structure_output":
        response = await llm.astructured_output(messages=messages, constraint=constraint)
    elif type == "select_tool":
        response = await llm.aselect_tool(messages=messages, tools=tools, tool_choice=tool_choice)
    else:
        raise ValueError(f"Invalid type: {type}")
    return response


def llm_worker(
    model: str,
    messages: t.List[Message], 
    *,
    tools: t.List[Tool] = [],
    tool_choice: t.Literal["auto", "required", "none"] = "auto",
    timeout: int = 120,
    max_tokens: int = 2048,
    type: str = "chat",
    constraint: Constraint = None,
    **kwargs: t.Any
) -> Response:
    # 从环境变量读取 API 配置
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY 环境变量未设置。请设置环境变量或创建 .env 文件。"
            "参考 .env.example 文件了解如何配置。"
        )
    
    llm = OpenAILlm(
        api_base=api_base,
        api_key=api_key,
        configuration=OpenAIConfiguration(
            model=model,
            temperature=0.0,
            max_tokens=max_tokens,
            **kwargs
        ),
        timeout=timeout,
    )
    if type == "chat":
        response = llm.chat(messages=messages)
    elif type == "structure_output":
        response = llm.structured_output(messages=messages, constraint=constraint)
    elif type == "select_tool":
        response = llm.select_tool(messages=messages, tools=tools, tool_choice=tool_choice)
    else:
        raise ValueError(f"Invalid type: {type}")
    return response


########################################################################################################################
# 测试
########################################################################################################################


async def test_llm_worker():
    model = "openai/gpt-5-nano"
    try:
        response = await llm_worker(
            model=model,
            messages=[
                Message.from_text("You are a hulpful assistant!", role=Role.SYSTEM),
                Message.from_text("Introduce yourself briefly", role=Role.USER)
            ],
            timeout=120,
            max_tokens=2048
        )
        print(response.message.content)
        print(f'正常访问模型: {model}')
    except Exception as e:
        print(f'不能正常访问模型: {model}')
        print(e)

    print()
    print("- " * 30)
    print()

    # 嵌套的 Pydantic 模型在 OpenAI 使用 structured_output 时，
    # 需要使用 json_json_schema_extra 来指定 required 和 additionalProperties
    class MyModel(BaseModel):
        model_config = {
            "extra": "forbid",
            "json_json_schema_extra": {
                "required": ["name", "age"],
                "additionalProperties": False,
            }
        }
        name: str
        age: int

    class MyModels(BaseModel):
        model_config = {
            "extra": "forbid",
            "json_json_schema_extra": {
                "required": ["models"],
                "additionalProperties": False,
            }
        }
        models: t.List[MyModel]

    try:
        response = await llm_worker(
            model=model,
            messages=[
                Message.from_text("extract the name and age from the following text", role=Role.SYSTEM),
                Message.from_text("My name is John and I am 30 years old\nHis name is Jane and I am 25 years old", role=Role.USER)
            ],
            type="structure_output",
            constraint=PydanticModel(model=MyModels),
            timeout=120,
            max_tokens=2048
        )
        print(response.model_dump_json(indent=4))
        print(f'正常访问模型: {model}')
    except Exception as e:
        print(f'不能正常访问模型: {model}')
        print(e)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_llm_worker())

    