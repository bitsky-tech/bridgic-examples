"""
Example 3: Dynamic Topology (Declarative API)

Bridgic introduces a novel orchestration model built on a DDG (Dynamic Directed Graph),
in which the graph topology can be modified at runtime. A typical use case is dynamically
instantiating workers based on the number of items in a list returned by a previous task.

This example uses the declarative GraphAutoma API (no ASL).
"""
from typing import List
from bridgic.core.automa import GraphAutoma, worker, RunningOptions
from bridgic.core.automa.args import ArgsMappingRule


class DynamicGraph(GraphAutoma):
    """A dynamic graph that creates handlers based on the number of tasks."""
    
    @worker(is_start=True)
    async def produce_task(self, user_input: int) -> List[int]:
        """
        Produce a list of tasks and dynamically create handlers for each task.
        """
        tasks = [i for i in range(user_input)]
        handler_keys = []
        
        # Dynamically create task handlers for each task
        for task in tasks:
            handler_key = f"handler_{task}"
            self.add_func_as_worker(
                key=handler_key,
                func=self.task_handler
            )
            # Use ferry_to to trigger each handler with its corresponding task
            self.ferry_to(handler_key, sub_task=task)
            # Collect the keys of handlers
            handler_keys.append(handler_key)
        
        # Create a collector worker that depends on all dynamic handlers
        self.add_func_as_worker(
            key="collect",
            func=self.collect,
            dependencies=handler_keys,
            args_mapping_rule=ArgsMappingRule.MERGE,
            is_output=True
        )
        
        return tasks

    async def task_handler(self, sub_task: int) -> int:
        """Handle a single sub-task."""
        res = sub_task + 1
        return res

    async def collect(self, res_list: List[int]) -> List[int]:
        """Collect results from all task handlers."""
        return res_list


async def main():
    dynamic_graph = DynamicGraph(running_options=RunningOptions(debug=True))
    result = await dynamic_graph.arun(user_input=3)
    print(f"Result: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
