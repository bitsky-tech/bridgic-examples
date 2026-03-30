"""
Example 7: CliAutoma with MCP Integration

Demonstrates how to build an interactive CLI automa using MCP (Model Context Protocol).
This example shows how to:
- Connect to a CLI MCP server
- Build an automa that supports human-in-the-loop interactions
- Handle interrupt-resume cycles for multi-turn interactions
- Reuse MCP connections across multiple execution cycles

This example specifically simulates multi-turn human-computer interactions by mimicking
user command input. In real-world development, developers can customize their own
human-in-the-loop interaction flow as needed.
"""
import os
import uuid
import tempfile
import dotenv

import mcp

from bridgic.core.automa import GraphAutoma, worker, RunningOptions
from bridgic.core.automa.interaction import Event, InteractionFeedback, InteractionException
from bridgic.core.utils._console import printer
from bridgic.protocols.mcp import (
    McpServerConnectionStdio,
    McpServerConnectionManager,
)

dotenv.load_dotenv()


# Create a temporary directory for the CLI MCP server
temp_dir = os.path.realpath(tempfile.mkdtemp())
print(f"Using temporary directory: {temp_dir}")

# Create a file with written content for demonstration
with open(os.path.join(temp_dir, "dream.txt"), "w", encoding="utf-8") as f:
    f.write("Bridging Logic and Magic")

# Connect to CLI MCP server
# Note: This requires uvx to be installed (or use npx with @modelcontextprotocol/server-cli)
cli_connection = McpServerConnectionStdio(
    name="connection-cli-stdio",
    command="uvx",
    args=["cli-mcp-server"],
    env={
        "ALLOWED_DIR": temp_dir,
        "ALLOWED_COMMANDS": "ls,cat,wc,pwd,echo,touch",
        "ALLOWED_FLAGS": "all",
        "ALLOW_SHELL_OPERATORS": "true",
    },
)

# Register the connection with a dedicated manager
# This allows isolation from other MCP connections
McpServerConnectionManager.get_instance("terminal-use").register_connection(cli_connection)

# Note: registration must be done before calling connect()
cli_connection.connect()

print(f"✓ Connected to CLI MCP server: {cli_connection.name}")
print(f"  Connection status: {cli_connection.is_connected}\n")


class CliAutoma(GraphAutoma):
    """
    An interactive CLI automa that supports human-in-the-loop interactions.
    
    The automa:
    - Welcomes the user
    - Requests commands via interact_with_human()
    - Executes commands using MCP CLI tools
    - Supports interrupt-resume cycles for multi-turn interactions
    - Reuses the same MCP connection across all cycles
    """
    
    @worker(is_start=True)
    def start(self):
        """Start the CLI automa and request the first command."""
        printer.print(f"Welcome to the example CLI Automa.", color="gray")
        self.ferry_to("human_input")

    @worker()
    def human_input(self):
        """
        Handle human input through interrupt-resume mechanism.
        
        - On first run: pauses (raising InteractionException)
        - On resume: receives feedback (the human command) and continues
        """
        # Interrupt-resume:
        # - on first run this pauses (raising InteractionException);
        # - on resume we receive feedback (the human command) and continue.
        event = Event(event_type="get_human_command")
        feedback: InteractionFeedback = self.interact_with_human(event)
        human_command = feedback.data

        printer.print(f"> {human_command}")

        if human_command in ["quit", "exit"]:
            self.ferry_to("end")
        else:
            # Generate unique keys for dynamic workers
            tool_key = f"tool-<{uuid.uuid4().hex[:8]}>"
            collect_key = f"collect-<{uuid.uuid4().hex[:8]}>"

            async def _collect_command_result(command_result: mcp.types.CallToolResult):
                """Collect and display the command result, then request next command."""
                printer.print(f"{command_result.content[0].text.strip()}\n", color="gray")
                self.ferry_to("human_input")

            # Reuse the same connection across all interrupt-resume cycles.
            # It was established once and stays open.
            # Each turn we fetch it here and it outlives cycle of running.
            real_connection = McpServerConnectionManager.get_connection("connection-cli-stdio")

            # Filter the "run_command" tool spec from cli-mcp-server.
            command_tool = next(t for t in real_connection.list_tools() if t.tool_name == "run_command")

            # Use the tool specification to create worker instance and then add it dynamically.
            self.add_worker(tool_key, command_tool.create_worker())
            self.add_func_as_worker(collect_key, _collect_command_result, dependencies=[tool_key])
            self.ferry_to(tool_key, command=human_command)

    @worker(is_output=True)
    def end(self):
        """End the CLI automa session."""
        printer.print(f"See you again.\n", color="gray")


async def main():
    """
    Main function demonstrating the CliAutoma usage.
    
    The lifecycle of an MCP server connection is independent from the execution
    of an automa: neither interact_with_human() (which pauses and raises
    InteractionException) nor arun() / arun(feedback_data=...) (which runs or
    resumes the automa) affects the connection. Once a connection is established
    and managed by a connection manager, it remains open until you close it.
    
    A practical implication is that one connection can serve many executions,
    which is important for the development of application. The automa may pause
    at interact_with_human() and be resumed later with arun(feedback_data=...);
    each cycle can use MCP tools over the same connection without reconnecting.
    """
    hi_automa = CliAutoma(
        name="human-interaction-automa",
        running_options=RunningOptions(debug=False)
    )

    interaction_id = None

    async def continue_automa(feedback_data=None) -> str:
        """Helper function to run or resume the automa."""
        try:
            await hi_automa.arun(feedback_data=feedback_data)
        except InteractionException as e:
            interaction_id = e.interactions[0].interaction_id
            return interaction_id

    # First run: automa reaches human_input, calls interact_with_human, pauses (InteractionException).
    # We obtain interaction_id for the next resume.
    interaction_id = await continue_automa()

    # Each iteration we send the human command as feedback to resume the execution.
    commands = [
        "pwd",
        "ls -l",
        "wc -l ./dream.txt",
        "cat ./dream.txt",
        "exit",
    ]
    
    for command in commands:
        interaction_feedback = InteractionFeedback(
            interaction_id=interaction_id,
            data=command
        )
        interaction_id = await continue_automa(interaction_feedback)

    # Close the connection when done
    cli_connection.close()
    print(f"✓ Connection closed: {not cli_connection.is_connected}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
