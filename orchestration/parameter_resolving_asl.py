"""
Example 4: Parameter Resolving

Demonstrates the capability of parameter resolving. A RAG-based question-answering system:
the user input is processed through two concurrent retrieval paths—keyword search and semantic search.
Each path retrieves a set of chunks, which are then merged and used to generate a retrieval-augmented response.
"""
import os
import dotenv

from typing import List, Tuple
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Message
from bridgic.asl import ASLAutoma, graph, Settings
from bridgic.core.automa import RunningOptions
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

async def pre_process(user_input: str) -> str:
    return user_input.strip()

async def keyword_search(query: str) -> List[str]:
    # Simulate keyword search by returning a fixed list of chunks.
    chunks = [
        "Albert Einstein was born on March 14, 1879, in Ulm, in the Kingdom of Württemberg, Germany  (now simply part of modern Germany).",
        "Einstein was born into a secular Jewish family Biography.",
        "Einstein had one sister, Maja, who was born two years after him.",
    ]
    return chunks

async def semantic_search(query: str) -> List[str]:
    # Simulate semantic search by returning a fixed list of chunks.
    chunks = [
        "Albert Einstein was born on March 14, 1879, in Ulm, in the Kingdom of Württemberg in the German Empire (now part of Germany).",
        "Shortly after his birth, his family moved to Munich, where he spent most of his childhood.",
        "Einstein excelled at physics and mathematics from an early age, teaching himself algebra, calculus, and Euclidean geometry by age twelve.",
    ]
    return chunks

async def synthesize_response(
    search_results: Tuple[List[str], List[str]], 
    query: str = From("pre_process")
) -> str:
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

class RAGProcessor(ASLAutoma):
    with graph as g:
        pre_process = pre_process
        k = keyword_search
        s = semantic_search
        output = synthesize_response *Settings(args_mapping_rule=ArgsMappingRule.MERGE)
        
        +pre_process >> (k & s) >> ~output

async def main():
    rag = RAGProcessor(running_options=RunningOptions(debug=True))
    result = await rag.arun(user_input="When and where was Einstein born?")
    print(f"{result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
