import json
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple, Union

from bridgic.core.model.types import Role, Message, ToolCall
from bridgic.core.model.protocols import PydanticModel
from bridgic.core.automa import GraphAutoma, worker
from bridgic.core.automa.args import InOrder, ArgsMappingRule
from bridgic.core.agentic.tool_specs import ToolSpec


# add project root to python path
import sys
from pathlib import Path
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
from browser_use.tools import read_tool_spec, search_tool_spec, get_search_results_tool_spec
from browser_use.tools.llm_tool import llm_worker, allm_worker



class Goal(BaseModel):
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "required": ["goal", "reasoning"],
            "additionalProperties": False,
        }
    }
    goal: str
    reasoning: str

    def __str__(self) -> str:
        return json.dumps({
            "goal": self.goal,
            "reasoning": self.reasoning
        }, ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()


class ActionIntent(BaseModel):
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "required": ["actions", "reasoning"],
            "additionalProperties": False
        }
    }
    actions: List[ToolCall]
    reasoning: str
    result: Optional[str] = None


class MemorySystem(BaseModel):
    """
    四层记忆系统
    
    - goal_memory: 目标记忆，记录动态生成的目标
    - experience_memory: 经验记忆，记录历史经验和最佳实践
    - world_memory: 世界记忆，包含角色定义(whoami)和工具列表(tools)
    - work_memory: 工作记忆，包含当前观察、历史记录等运行时信息
    """
    goal_memory: Goal = None  # 目标记忆
    experience_memory: List[str] = []  # 经验记忆
    world_memory: Dict[str, Any] = {}  # 世界记忆（包含whoami和tools）
    work_memory: Dict[str, Any] = {}  # 工作记忆（包含observation、history等）

    def __str__(self) -> str:
        return json.dumps({
            "goal_memory": self.goal_memory,
        }, ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()


class CognitionState(BaseModel):
    observation: str
    memory: MemorySystem
    is_finished: bool = False


class CognitionStrategy(ABC):
    """
    Cognition strategy is the core of the agent. It is responsible for reasoning about what the agent will do next.
    """

    # TODO: It is necessary to consider what approach the model invocation takes in this CognitionStrategy.
    def __init__(self, model):
        self.model = model
    
    @abstractmethod
    async def reason(
        self,
        state: CognitionState
    ) -> ActionIntent:
        """
        Reason about what the agent will do next based on the current state.
        
        Parameters
        ----------
        state : CognitionState
            The current cognition state.

        Returns
        -------
        ActionIntent:
            The action intent.
        """
        pass


class ReActStrategy(CognitionStrategy):
    """
    ReAct strategy is a simple strategy that reason about what the agent will do next based on the current state.
    """
    async def reason(
        self,
        state: CognitionState
    ) -> ActionIntent:
        """
        Reason about what the agent will do next based on the current state.
        
        Parameters
        ----------
        state : CognitionState
            The current cognition state.

        Returns
        -------
        ActionIntent:
            The action intent.
        """
        # Get the available tools.
        available_tools = [tool.to_tool() for tool in state.memory.world_memory.get("tools", [])]

        # Build the system prompt.
        experience_memory = '\n'.join([f"- {exp}" for exp in state.memory.experience_memory])
        system_prompt = (
            f"{state.memory.world_memory.get('whoami', '')}\n\n"
            f"You have learned the following experience in the past:\n"
            f"{experience_memory}\n\n"
        )

        # Build the context for the ReAct strategy.
        context = (
            f"You are now working towards this overall goal.: {state.memory.goal_memory.goal}\n\n"
            f"After the previous step is completed, you now receive feedback: {state.observation}\n\n"
            f"If you think the current task is completed, please output only 'EXIT' and nothing else. \n\n"
            f"Otherwise, please reason about what should do next."
            f"**Only return the brief and concise reasoning.**"
        )

        # Invoke the model to reason about what the agent will do next.
        messages = [
            Message.from_text(text=system_prompt, role=Role.SYSTEM),
            Message.from_text(text=context, role=Role.USER),
        ]
        # print('-' * 50)
        # for message in messages:
        #     print(f"[{message.role}] {message.content}")
        # print('-' * 50 + '\n\n')

        response = await allm_worker(
            model=self.model,
            messages=messages,
            timeout=120,
            max_tokens=8192
        )
        reasoning = response.message.content
        if "EXIT" in reasoning:
            state.memory.work_memory["is_finished"] = True

        context = (
            f"You are now working towards this overall goal.: {state.memory.goal_memory.goal}\n\n"
            f"After the previous step is completed, you now receive feedback: {state.observation}\n\n"
            f"Now, there is the current step: {reasoning}.\n\n"
        )
        messages = [
            Message.from_text(text=system_prompt, role=Role.SYSTEM),
            Message.from_text(text=context, role=Role.USER),
        ]
        # print('-' * 50)
        # for message in messages:
        #     print(f"[{message.role}] {message.content}")
        # print('-' * 50 + '\n\n')

        tool_calls, response = await allm_worker(
            model=self.model,
            messages=messages,
            type="select_tool",
            tools=available_tools,
            tool_choice="auto",
            timeout=120,
            max_tokens=8192
        )
        result = response

        return ActionIntent(
            actions=tool_calls,
            reasoning=reasoning,
            result=result
        )


class Agent(GraphAutoma):
    def __init__(self, cognition_strategy: CognitionStrategy, model):
        # Initialize the graph automa
        super().__init__()

        # The original system variables
        self.user_input = None

        # The agentic system variables
        # TODO: 1. Should check the duplicate tool specs between the builtin tool specs and the user-defined tool specs.
        self.model = model
        self.cognition_strategy = cognition_strategy
        self.cognition_strategy.model = model
        self.memory_system = MemorySystem(
            goal_memory=Goal(goal="", reasoning=""),
            experience_memory=[],
            world_memory={},
            work_memory={
                "observation": "",
                "history": [],
                "loop_count": 0,
                "max_loops": 20,
                "is_finished": False,
                "is_first": True
            }
        )

    #########################################################
    ################ Built-in thinking tools ################
    #########################################################
    
    @staticmethod
    async def _generate_goal(memory: MemorySystem, observation: str) -> str:
        """
        Generate a goal to solve the given observation

        Parameters
        ----------
        observation : str
            The observation to generate a goal for

        Returns
        -------
        str:
            The generated goal
        """
        experience_memory = '\n'.join([f"- {exp}" for exp in memory.experience_memory])
        messages = [
            Message.from_text(
                text=(
                    f"{memory.world_memory.get('whoami', '')}\n\n"
                    f"I have learned the following experience in the past:\n"
                    f"{experience_memory}\n\n"
                    f"Now, given the new observation, I need to generate a goal to solve it.\n\n"
                    f"**Only return the brief and concise goal.**\n\n"
                ),
                role=Role.SYSTEM
            ),
            Message.from_text(text=f"{observation}\n\n", role=Role.USER)
        ]
        response = await allm_worker(
            model="gpt-4o-mini",
            messages=messages,
            type="structure_output",
            constraint=PydanticModel(model=Goal),
            timeout=120,
            max_tokens=8192
        )
        return response

    async def _generate_final_answer(self, final_result: str):
        """
        Generate the final answer based on the history and the final result.
        """
        experience_memory = '\n'.join([f"- {exp}" for exp in self.memory_system.experience_memory])
        messages = [
            Message.from_text(
                text=(
                    f"{self.memory_system.world_memory.get('whoami', '')}\n\n"
                    f"I have learned the following experience in the past:\n"
                    f"{experience_memory}\n\n"
                    f"Now, given the final result, I need to generate a final answer.\n\n"
                    f"**Only return the brief and concise final answer.**\n\n"
                ),
                role=Role.SYSTEM
            ),
            Message.from_text(text=f"{final_result}\n\n", role=Role.USER)
        ]
        response = await allm_worker(
            model="gpt-4o-mini",
            messages=messages,
            timeout=120,
            max_tokens=8192
        )
        return response.message.content

    #########################################################
    ############### Private utility functions ###############
    #########################################################

    def _match_tool_calls_and_tool_specs(
        self,
        tool_calls: List[ToolCall],
        tool_spec_list: List[ToolSpec],
    ) -> List[Tuple[ToolCall, ToolSpec]]:
        """
        This function is used to match the tool calls and the tool specs based on the tool name.

        Parameters
        ----------
        tool_calls : List[ToolCall]
            The tool calls to match.
        tool_spec_list : List[ToolSpec]
            The tool specs to match.

        Returns
        -------
        List[(ToolCall, ToolSpec)]
            The matched tool calls and tool specs.
        """
        # print(f"[Match] Tool calls: {tool_calls}, tool specs: {tool_spec_list}")
        matched_list: List[Tuple[ToolCall, ToolSpec]] = []
        for tool_call in tool_calls:
            for tool_spec in tool_spec_list:
                if tool_call.name == tool_spec.tool_name:
                    matched_list.append((tool_call, tool_spec))
        return matched_list

    @staticmethod
    async def _merge_results(results: List[Any]) -> Any:
        """
        Merge the results from the tool calls.
        """
        return results

    #########################################################
    ############ Perception-Cognition-Action Loop ###########
    #########################################################

    @worker(is_start=True)
    async def perception(self, input_data: Union[str, dict]) -> str:
        # TODO: Process the input data, will be expanded in the future
        #   1. Obtaining the execution results of various tools, directly using all the results as observations 
        #      may not be entirely appropriate. In some specific scenarios, it is only necessary to know a certain signal. 
        #      Therefore, here, perception determines how to organize the execution results of the tools.
        #   2. The interface should be open to allow for free customization in the future.
        if self.memory_system.work_memory.get("is_first", True):
            observation = input_data
        else:
            tool_names = [tool_name for tool_name, _ in input_data.get('results', [])]
            observation = (
                f"The last step: {input_data.get('action', '')} is successfully executed with tools: {tool_names}."
                f"The results of the tools are: "
                f"{input_data.get('results', [])}"    
            )
        print(f"[Perception] Observation: length {len(observation)}, preview: {observation[:300]}")
        return observation
    
    @worker(dependencies=["perception"])
    async def cognition(self, observation: str) -> dict:
        # TODO: If the agent is finished, return empty dict, should be a more robust implementation.
        if self.memory_system.work_memory.get("is_finished", False):
            return {}
        
        # TODO: The learning process that alters internal states directly manipulates the core concepts of memory.
        #   1. Should have a interface like `reason` to let user can override the cognition strategy.
        #   2. ...
        # first time to call perception, initialize the memory system, and generate the goal
        is_first = self.memory_system.work_memory.get("is_first", True)
        if is_first:
            self.memory_system.work_memory['user_input'] = observation
            self.memory_system.work_memory["observation"] = observation
            self.memory_system.work_memory["is_finished"] = False
            self.memory_system.work_memory["is_first"] = False
            self.memory_system.work_memory["loop_count"] = 0
            self.memory_system.goal_memory = await self._generate_goal(self.memory_system, observation)

        # Reason about what the agent will do next.
        state = CognitionState(
            observation=observation,
            memory=self.memory_system,
            is_finished=self.memory_system.work_memory.get("is_finished", False)
        )
        action_intent = await self.cognition_strategy.reason(state)

        # Trigger termination
        # TODO:
        # When does the agent stop and output the final response provided to the user?
        #   1. ...
        pass
        
        print(f"[Cognition] Action intent: {action_intent}")
        return action_intent
    
    @worker(dependencies=["cognition"], is_output=True)
    async def action(self, action_intent: ActionIntent) -> str:
        # TODO: If the agent is finished, generate the final answer and return it, should be a more robust implementation in the future?
        if self.memory_system.work_memory.get("is_finished", False):
            last_observation = self.memory_system.work_memory.get("observation", "")
            final_answer = await self._generate_final_answer(last_observation)
            return final_answer

        # Collect matching tools. Must match the tool calls and the tool specs, otherwise the action is meaningless.
        actions = action_intent.actions
        matched_list = self._match_tool_calls_and_tool_specs(actions, self.memory_system.world_memory.get("tools", [])) or []
        matched_tool_calls = []
        if matched_list:
            # Execute the actions in a sandbox.
            # TODO: 
            # Currently, a concurrent is used as the container. In the future, there should be some abstractions 
            # for the sandbox and the action runtime environment.
            sand_box = GraphAutoma()
            worker_keys = []
            for tool_call, tool_spec in matched_list:
                matched_tool_calls.append(tool_call)
                tool_worker = tool_spec.create_worker()
                worker_key = f"tool_{tool_call.name}_{tool_call.id}"
                sand_box.add_worker(
                    key=worker_key,
                    worker=tool_worker,
                    is_start=True,
                    args_mapping_rule=ArgsMappingRule.UNPACK
                )
                worker_keys.append(worker_key)
            sand_box.add_func_as_worker(
                key="__merge__",
                func=Agent._merge_results,
                dependencies=worker_keys,
                args_mapping_rule=ArgsMappingRule.MERGE,
                is_output=True
            )
            print(f"[Action] Matched tool calls: {matched_tool_calls}")
            matched_tool_calls_args = [tool_call.arguments for tool_call in matched_tool_calls]
            results = await sand_box.arun(InOrder(matched_tool_calls_args))
        else:
            results = [action_intent.result]

        # Update historical information
        action_result = {
            "observation": self.memory_system.work_memory.get("observation", ""),
            "action": action_intent.reasoning,
            "results": [
                (tool.name, tool_result) 
                for tool, tool_result in zip(matched_tool_calls, results)]
        }
        self.memory_system.work_memory["history"].append(action_result)

        # Check the loop count and the finished state
        self.memory_system.work_memory["loop_count"] = self.memory_system.work_memory.get("loop_count", 0) + 1
        max_loops = self.memory_system.work_memory.get("max_loops", 20)
        if self.memory_system.work_memory["loop_count"] >= max_loops:
            print(f"[Warning] Reached the maximum loop count {max_loops}, stop the loop")
            self.memory_system.work_memory["is_finished"] = True
        
        # Return to perception to continue the loop
        print(f"[Action] Action completed, return to perception to continue the loop (第 {self.memory_system.work_memory['loop_count']} 轮)\n\n")
        self.ferry_to("perception", action_result)


########################################################################################################################
# 使用示例
########################################################################################################################
import asyncio


async def example_react():
    """示例：使用ReAct策略，带完整的记忆系统"""
    agent = Agent(ReActStrategy("gpt-4o-mini"), model="gpt-4o-mini")
    
    # 初始化记忆系统
    agent.memory_system.experience_memory = [
        "The website https://zhidao.baidu.com/ is a popular question and answer website.",
        # "The website https://www.toutiao.com/ is a popular question and answer website.",
        # "The website https://www.sina.com.cn/ is a popular question and answer website.",
        (
            "When the task requires information collection, there is such a process that can be used:\n"
            "- 1. Use the SearchTool to search for the information on websites\n"
            "- 2. Use the GetSearchResultsTool to get the search results.\n\n"
            "After following the above steps, what you get is just a summary of the search results. "
            "You need to extract the article links from it and then use ReadTool to obtain the content "
            "of these articles."
        )
    ]
    agent.memory_system.world_memory["whoami"] = (
        f'You are a network information analysis assistant. When the user inputs a question,' 
        f'you will collect relevant information from the internet and answer the question.'
    )
    agent.memory_system.world_memory["tools"] = [
        read_tool_spec, 
        search_tool_spec,
        get_search_results_tool_spec
    ]
    
    res = await agent.arun("怎么挑选家用电脑的键盘？")
    print(f"[Example] Final answer: {res}")


if __name__ == "__main__":
    # 运行示例
    print("=" * 50)
    print("示例1: ReAct策略")
    print("=" * 50)
    asyncio.run(example_react())