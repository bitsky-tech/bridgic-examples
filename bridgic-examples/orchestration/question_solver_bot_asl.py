"""
Example 1: ASL (Agent Structure Language) - QuestionSolverBot

A QuestionSolverBot that merges individual answers into a unified response.
Reuses DivideConquerWorkflow in a component-oriented fashion.
"""
import os
import dotenv

from typing import List, Dict
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.automa import RunningOptions
from bridgic.core.model.types import Message
from bridgic.asl import ASLAutoma, graph

dotenv.load_dotenv()

# Get the API key and model name from environment variables.
_api_key = os.environ.get("OPENAI_API_KEY")
_model_name = os.environ.get("OPENAI_MODEL_NAME")

llm = OpenAILlm(
    api_key=_api_key,
    timeout=5,
    configuration=OpenAIConfiguration(model=_model_name),
)

# Break down the query into a list of sub-queries.
async def break_down_query(user_input: str) -> List[str]:
    llm_response = await llm.achat(
        messages=[
            Message.from_text(text="Break down the query into multiple sub-queries and only return the sub-queries", role="system"),
            Message.from_text(text=user_input, role="user"),
        ]
    )
    return [item.strip() for item in llm_response.message.content.split("\n") if item.strip()]

# Generate answers for each sub-query.
async def query_answer(queries: List[str]) -> Dict[str, str]:
    answers = []
    for query in queries:
        response = await llm.achat(
            messages=[
                Message.from_text(text="Answer the given query briefly", role="system"),
                Message.from_text(text=query, role="user"),
            ]
        )
        answers.append(response.message.content)
    
    res = {
        query: answer
        for query, answer in zip(queries, answers)
    }
    return res

class DivideConquerWorkflow(ASLAutoma):
    with graph as g:
        a = break_down_query
        b = query_answer

        +a >> ~b

async def merge_answers(qa_pairs: Dict[str, str], user_input: str) -> str:
    answers = "\n".join([v for v in qa_pairs.values()])
    llm_response = await llm.achat(
        messages=[
            Message.from_text(text=f"Answer the question in bullet points.", role="system"),
            Message.from_text(text=f"Question: {user_input}\nAnswers: {answers}", role="user"),
        ]
    )
    return llm_response.message.content

# Define the QuestionSolverBot agent, reuse `DivideConquerWorkflow` in a component-oriented fashion.
class QuestionSolverBot(ASLAutoma):
    with graph as g:
        a = DivideConquerWorkflow()
        b = merge_answers

        +a >> ~b

async def main():
    chatbot = QuestionSolverBot(running_options=RunningOptions(debug=True))
    answer = await chatbot.arun(user_input="When and where was Einstein born?")
    print(answer)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
