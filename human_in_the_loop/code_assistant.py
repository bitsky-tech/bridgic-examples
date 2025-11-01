"""
This example demonstrates how to use the Bridgic framework to create a code assistant that can generate code, approve it by the user, and execute it.

Before running this example, you need to execute the following commands to set up the environment variables:

```shell
export OPENAI_API_KEY="<your_openai_api_key>"
export OPENAI_MODEL_NAME="<the_model_name>"
```

Run this example with uv:

```shell
uv run human_in_the_loop/code_assistant.py
```
"""

import os

# Get the API base, API key and model name.
_api_key = os.environ.get("OPENAI_API_KEY")
_api_base = os.environ.get("OPENAI_API_BASE")
_model_name = os.environ.get("OPENAI_MODEL_NAME")

from pydantic import BaseModel, Field
from bridgic.core.automa import GraphAutoma, worker
from bridgic.core.automa.args import From
from bridgic.core.automa.interaction import Event, Feedback, FeedbackSender
from bridgic.core.model.types import Message, Role
from bridgic.core.model.protocols import PydanticModel
from bridgic.llms.openai import OpenAILlm

# Set the LLM
llm = OpenAILlm(api_base=_api_base, api_key=_api_key, timeout=10)

class CodeBlock(BaseModel):
    code: str = Field(description="The code to be executed.")

class CodeAssistant(GraphAutoma):
    @worker(is_start=True)
    async def generate_code(self, user_requirement: str):
        response = await llm.astructured_output(
            model=_model_name,
            messages=[
                Message.from_text(text=f"You are a programming assistant. Please generate code according to the user's requirements.", role=Role.SYSTEM),
                Message.from_text(text=user_requirement, role=Role.USER),
            ],
            constraint=PydanticModel(model=CodeBlock)
        )
        return response.code

    @worker(dependencies=["generate_code"])
    async def ask_to_run_code(self, code: str):
        event = Event(event_type="can_run_code", data=code)
        feedback = await self.request_feedback_async(event)
        return feedback.data
        
    @worker(dependencies=["ask_to_run_code"])
    async def output_result(self, feedback: str, code: str = From("generate_code")):
        code = code.strip("```python").strip("```")
        if feedback == "yes":
            print(f"- - - - - - Result - - - - - -")
            exec(code)
            print(f"- - - - - - End - - - - - -")
        else:
            print(f"This code was rejected for execution. In response to the requirements, I have generated the following code:\n```python\n{code}\n```")

# Handle can_run_code event
def can_run_code_handler(event: Event, feedback_sender: FeedbackSender):
    print(f"Can I run this code now to verify if it's correct?")
    print(f"```python\n{event.data}\n```")
    res = input("Please input your answer (yes/no): ")
    if res in ["yes", "no"]:
        feedback_sender.send(Feedback(data=res))
    else:
        print("Invalid input. Please input yes or no.")
        feedback_sender.send(Feedback(data="no"))

# register can_run_code event handler to `CodeAssistant` automa
code_assistant = CodeAssistant()
code_assistant.register_event_handler("can_run_code", can_run_code_handler)

async def main():
    await code_assistant.arun(user_requirement="Please write a function to print 'Hello, World!' and run it.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())