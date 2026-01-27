"""
Example 4: Parameter Resolving (Declarative API)

Demonstrates the capability of parameter resolving. A RAG-based question-answering system:
the user input is processed through two concurrent retrieval paths—keyword search and semantic search.
Each path retrieves a set of chunks, which are then merged and used to generate a retrieval-augmented response.

This example uses the declarative GraphAutoma API (no ASL).
"""
import os
import dotenv

from typing import List, Tuple, Optional
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Message
from bridgic.core.automa import GraphAutoma, worker, RunningOptions
from bridgic.core.automa.args import ArgsMappingRule, From

dotenv.load_dotenv()

# Get the API key and model name from environment variables.
_api_key = os.environ.get("OPENAI_API_KEY")
_model_name = os.environ.get("OPENAI_MODEL_NAME")

llm = OpenAILlm(
    api_key=_api_key,
    timeout=5,
    configuration=OpenAIConfiguration(model=_model_name),
)


class RAGProcessor(GraphAutoma):
    """A RAG processor that uses keyword and semantic search, then synthesizes the results."""
    
    @worker(is_start=True)
    async def pre_process(self, user_input: str) -> str:
        """Pre-process the user input."""
        return user_input.strip()

    @worker(dependencies=["pre_process"])
    async def keyword_search(self, query: str) -> List[str]:
        """Simulate keyword search by returning a fixed list of chunks."""
        chunks = [
            "Albert Einstein was born on March 14, 1879, in Ulm, in the Kingdom of Württemberg, Germany  (now simply part of modern Germany).",
            "Einstein was born into a secular Jewish family Biography.",
            "Einstein had one sister, Maja, who was born two years after him.",
        ]
        return chunks

    @worker(dependencies=["pre_process"])
    async def semantic_search(self, query: str) -> List[str]:
        """Simulate semantic search by returning a fixed list of chunks."""
        chunks = [
            "Albert Einstein was born on March 14, 1879, in Ulm, in the Kingdom of Württemberg in the German Empire (now part of Germany).",
            "Shortly after his birth, his family moved to Munich, where he spent most of his childhood.",
            "Einstein excelled at physics and mathematics from an early age, teaching himself algebra, calculus, and Euclidean geometry by age twelve.",
        ]
        return chunks

    @worker(
        dependencies=["keyword_search", "semantic_search"],
        args_mapping_rule=ArgsMappingRule.MERGE,
        is_output=True
    )
    async def synthesize_response(
        self,
        search_results: Tuple[List[str], List[str]],
        query: str = From("pre_process")
    ) -> str:
        """
        Synthesize a response from the search results.
        
        The search_results tuple contains results from both keyword_search and semantic_search,
        merged via ArgsMappingRule.MERGE. The query parameter is injected from pre_process
        using From("pre_process").
        """
        chunks_by_keyword, chunks_by_semantic = search_results
        all_chunks = chunks_by_keyword + chunks_by_semantic
        prompt = f"{query}\n---\nAnswer the above question based on the following references.\n{all_chunks}"
        llm_response = await llm.achat(
            messages=[
                Message.from_text(text="You are a helpful assistant", role="system"),
                Message.from_text(text=prompt, role="user"),
            ]
        )
        return llm_response.message.content


async def main():
    rag = RAGProcessor(running_options=RunningOptions(debug=True))
    result = await rag.arun(user_input="When and where was Einstein born?")
    print(f"{result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
