"""
This example demonstrates how to trace a multi-level nested workflow using `langwatch`
in `bridgic`.

Set up the environment variables:

```shell
export LANGWATCH_API_KEY="<your_langwatch_api_key>"
```

Run this example with uv:

```shell
uv run trace/workflow_nested_tracing.py
```
"""

import asyncio
from bridgic.traces.langwatch import start_langwatch_trace
from bridgic.core.automa import GraphAutoma, worker

# Configure tracing with `langwatch` in `bridgic`.
start_langwatch_trace()

# Define and create a multi-level nested workflow.

# Third level: ThirdWorkflow.
class ThirdWorkflow(GraphAutoma):
    @worker(is_start=True)
    async def workflow3_step1(self, x):
        await asyncio.sleep(0.3)
        return f"workflow3_step1 output"

    @worker(dependencies=["workflow3_step1"])
    async def workflow3_step2(self, x):
        await asyncio.sleep(0.3)
        return f"workflow3_step2 output"

    @worker(dependencies=["workflow3_step2"], is_output=True)
    async def workflow3_step3(self, x):
        await asyncio.sleep(0.3)
        return f"workflow3_step3 output"

# Create a ThirdWorkflow instance.
workflow3 = ThirdWorkflow()

# Second level: SecondWorkflow.
class SecondWorkflow(GraphAutoma):
    ...

# Create a SecondWorkflow instance.
workflow2 = SecondWorkflow()

@workflow2.worker(is_start=True)
async def workflow2_step1(x):
    await asyncio.sleep(0.2)
    return f"workflow2_step1 output"

workflow2.add_worker(
    key="workflow2_step2",
    worker=workflow3,
    dependencies=["workflow2_step1"],
)

@workflow2.worker(dependencies=["workflow2_step2"], is_output=True)
async def workflow2_step3(x):
    await asyncio.sleep(0.2)
    return f"workflow2_step3 output"

# First level: TopWorkflow.
class TopWorkflow(GraphAutoma):
    ...

# Create a TopWorkflow instance.
top_workflow = TopWorkflow()

top_workflow.add_worker(
    key="top_workflow_step1",
    worker=workflow2,
    is_start=True
)

@top_workflow.worker(dependencies=["top_workflow_step1"], is_output=True)
async def top_workflow_step2(x):
    await asyncio.sleep(0.1)
    return f"top_workflow_step2 output"

# Run the workflow.
async def main():
    await top_workflow.arun(x="top_workflow input")

if __name__ == "__main__":
    asyncio.run(main())