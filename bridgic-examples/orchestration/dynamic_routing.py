"""
Example 2: Dynamic Routing

The ferry_to() API enables an automa to dynamically decide which worker 
should run next, allowing the workflow to adapt its execution path based on runtime conditions.

This example uses the declarative GraphAutoma API (no ASL), and relies on
the ferry_to() orchestration pattern directly within worker methods.
"""
import os
import dotenv

from pydantic import BaseModel

from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Message
from bridgic.core.model.protocols import PydanticModel
from bridgic.core.automa import GraphAutoma, RunningOptions, worker

dotenv.load_dotenv()

# Get the API key and model name from environment variables.
_api_key = os.environ.get("OPENAI_API_KEY")
_model_name = os.environ.get("OPENAI_MODEL_NAME")

llm = OpenAILlm(
    api_key=_api_key,
    timeout=5,
    configuration=OpenAIConfiguration(model=_model_name),
)


class QueryCategory(BaseModel):
    """Classification result for a user query."""

    category: str
    """One of: 'questionn_answer' (question answering), 'createive_writing' (creative writing), 'code_writing' (code writing), 'unknown' (unrecognized)."""


class SimpleAssistant(GraphAutoma):
    @worker(is_start=True)
    async def router(self, request: str) -> str:
        """
        Classify the request into one of three categories and route to the corresponding handler:

        - questionn_answer: factual or explanatory question that should be answered directly
        - createive_writing: creative writing request (stories, poems, marketing copy, etc.)
        - code_writing: request to write or modify code, commands, or scripts
        - unknown: cannot be clearly mapped to the above categories
        """
        print(f"Routing request: {request}")

        classification: QueryCategory = await llm.astructured_output(
            constraint=PydanticModel(model=QueryCategory),
            messages=[
                Message.from_text(
                    text=(
                        "You are a classifier. Given a single user request, decide whether it is:\n"
                        "- 'questionn_answer': a factual or explanatory question to be answered directly;\n"
                        "- 'createive_writing': a creative writing instruction (story, poem, lyrics, copy, etc.);\n"
                        "- 'code_writing': a request to write or modify code, commands, or scripts;\n"
                        "- 'unknown': anything that does not clearly fit the above categories.\n"
                        "Respond ONLY with a JSON object that matches the schema, do not add explanations."
                    ),
                    role="system",
                ),
                Message.from_text(text=request, role="user"),
            ],
            model=_model_name,
        )

        category = classification.category

        if category == "questionn_answer":
            self.ferry_to("hq", question=request)
        elif category == "createive_writing":
            self.ferry_to("creative", instruction=request)
        elif category == "code_writing":
            self.ferry_to("code", instruction=request)
        else:
            self.ferry_to("unknown", original=request)

    @worker(key="hq", is_output=True)
    async def handle_question(self, question: str) -> str:
        print("❓ QUESTION")
        llm_response = await llm.achat(
            messages=[
                Message.from_text(
                    text=(
                        "You answer factual or explanatory questions. "
                        "Give a concise, accurate answer without unnecessary elaboration."
                    ),
                    role="system",
                ),
                Message.from_text(text=question, role="user"),
            ]
        )
        return llm_response.message.content

    @worker(key="creative", is_output=True)
    async def handle_creative(self, instruction: str) -> str:
        print("🎨 CREATIVE")
        llm_response = await llm.achat(
            messages=[
                Message.from_text(
                    text=(
                        "You are a creative writer. "
                        "Follow the user's instruction and create vivid, engaging content. "
                        "Keep the output reasonably short unless explicitly asked for long content."
                    ),
                    role="system",
                ),
                Message.from_text(text=instruction, role="user"),
            ]
        )
        return llm_response.message.content

    @worker(key="code", is_output=True)
    async def handle_code(self, instruction: str) -> str:
        print("💻 CODE")
        llm_response = await llm.achat(
            messages=[
                Message.from_text(
                    text=(
                        "You are a code assistant. "
                        "Write correct, minimal code or command-line snippets that satisfy the user's request. "
                        "Return only code or commands unless the user explicitly asks for explanation."
                    ),
                    role="system",
                ),
                Message.from_text(text=instruction, role="user"),
            ]
        )
        return llm_response.message.content

    @worker(key="unknown", is_output=True)
    async def handle_unknown(self, original: str) -> str:
        """
        Fallback handler for requests that cannot be clearly categorized.
        This worker intentionally does not call the LLM and simply returns the original request.
        """
        print("⚪ UNKNOWN")
        return original


async def main():
    router = SimpleAssistant(running_options=RunningOptions(debug=False))
    test_requests = [
        "When and where was Einstein born?",
        "Create a one-sentence poem about the spring season.",
        "Write a shell command to list all files in /bin directory.",
    ]
    for request in test_requests:
        print("=" * 80)
        response = await router.arun(request=request)
        print(f"{response.strip()}\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
