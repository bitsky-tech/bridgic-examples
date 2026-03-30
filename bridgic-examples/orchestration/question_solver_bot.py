"""
Example 1: QuestionSolverBot (Declarative API)

A QuestionSolverBot that merges individual answers into a unified response.
Reuses DivideConquerWorkflow in a component-oriented fashion.

This example uses the declarative GraphAutoma API (no ASL).
"""
import os
import dotenv

from typing import List, Dict, Optional
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Message
from bridgic.core.automa import GraphAutoma, worker, RunningOptions

dotenv.load_dotenv()

# Get the API key and model name from environment variables.
_api_key = os.environ.get("OPENAI_API_KEY")
_model_name = os.environ.get("OPENAI_MODEL_NAME")

llm = OpenAILlm(
    api_key=_api_key,
    timeout=5,
    configuration=OpenAIConfiguration(model=_model_name),
)


class DivideConquerWorkflow(GraphAutoma):
    """Break down a query into sub-queries and answer each one."""
    
    @worker(is_start=True)
    async def break_down_query(self, user_input: str) -> List[str]:
        """Break down the query into a list of sub-queries."""
        llm_response = await llm.achat(
            messages=[
                Message.from_text(
                    text="Break down the query into multiple sub-queries and only return the sub-queries",
                    role="system"
                ),
                Message.from_text(text=user_input, role="user"),
            ]
        )
        return [item.strip() for item in llm_response.message.content.split("\n") if item.strip()]

    @worker(dependencies=["break_down_query"], is_output=True)
    async def query_answer(self, queries: List[str]) -> Dict[str, str]:
        """Generate answers for each sub-query."""
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


# Define the QuestionSolverBot agent, reuse `DivideConquerWorkflow` in a component-oriented fashion.
class QuestionSolverBot(GraphAutoma):
    """A bot that solves questions by breaking them down and merging answers."""
    
    def __init__(self, name: Optional[str] = None, running_options: Optional[RunningOptions] = None):
        super().__init__(name=name, running_options=running_options)
        # Add DivideConquerWorkflow as a sub-automa
        divide_conquer = DivideConquerWorkflow()
        self.add_worker(
            key="divide_conquer_workflow",
            worker=divide_conquer,
            is_start=True
        )
        # Set dependency: merge_answers depends on divide_conquer_workflow
        self.add_dependency("merge_answers", "divide_conquer_workflow")
    
    @worker(is_output=True)
    async def merge_answers(self, qa_pairs: Dict[str, str], user_input: str) -> str:
        """Merge individual answers into a unified response."""
        answers = "\n".join([v for v in qa_pairs.values()])
        llm_response = await llm.achat(
            messages=[
                Message.from_text(text="Answer the question in bullet points.", role="system"),
                Message.from_text(text=f"Question: {user_input}\nAnswers: {answers}", role="user"),
            ]
        )
        return llm_response.message.content


async def main():
    chatbot = QuestionSolverBot(running_options=RunningOptions(debug=True))
    answer = await chatbot.arun(user_input="When and where was Einstein born?")
    print(answer)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
