"""
Example 3: Dynamic Topology

Bridgic introduces a novel orchestration model built on a DDG (Dynamic Directed Graph),
in which the graph topology can be modified at runtime. A typical use case is dynamically
instantiating workers based on the number of items in a list returned by a previous task.
"""
from typing import List
from bridgic.core.automa.args import ResultDispatchingRule
from bridgic.asl import ASLAutoma, graph, concurrent, Settings, ASLField

async def produce_task(user_input: int) -> List[int]:
    tasks = [i for i in range(user_input)]
    return tasks

async def task_handler(sub_task: int) -> int:
    res = sub_task + 1
    return res

class DynamicGraph(ASLAutoma):
    with graph(user_input=ASLField(type=int)) as g:
        producer = produce_task

        with concurrent(tasks = ASLField(type=list, dispatching_rule=ResultDispatchingRule.IN_ORDER)) as c:
            dynamic_handler = lambda tasks: (
                task_handler *Settings(key=f"handler_{task}")
                for task in tasks
            )

        +producer >> ~c

async def main():
    dynamic_graph = DynamicGraph()
    result = await dynamic_graph.arun(user_input=3)
    print(f"Result: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
