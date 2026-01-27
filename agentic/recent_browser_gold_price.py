"""
Example 8: Browser Automation with ReCentAutoma and Playwright MCP

Demonstrates how to integrate ReCentAutoma with MCP (Model Context Protocol) to create
a browser automation agent. This example uses the Playwright MCP server to enable the
agent to interact with browsers like Chrome autonomously to achieve user-defined goals.

This example shows how to:
- Connect to the Playwright MCP server via stdio transport for browser automation
- Register the connection using a dedicated Connection Manager to manage browser operations in isolation
- Create a ReCentAutoma agent loaded with browser automation tools
- Let the agent autonomously navigate to the Hong Kong Gold Exchange website and extract needed information

Steps overview:
1. Connect to the Playwright MCP server via stdio transport for browser automation capabilities
2. Register the connection using a dedicated Connection Manager to manage browser operations in isolation
3. Create a ReCentAutoma agent loaded with browser automation tools
4. Let the agent autonomously navigate to the Hong Kong Gold Exchange website and extract the needed information

If you're new to MCP, please check the MCP Quick Start tutorial for setup and usage instructions.
"""
import os
import tempfile
import dotenv

from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.automa import RunningOptions
from bridgic.core.agentic.recent import ReCentAutoma, ReCentMemoryConfig, StopCondition
from bridgic.protocols.mcp import (
    McpServerConnectionStdio,
    McpServerConnectionManager,
)

dotenv.load_dotenv()

# Get the API key and model name from environment variables
_api_key = os.environ.get("OPENAI_API_KEY")
_api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
_model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

async def main():
    """
    Main function demonstrating browser automation with ReCentAutoma and Playwright MCP.
    
    In this example, the agent autonomously uses a browser to navigate to the
    Hong Kong Gold Exchange website and search for the gold price. The entire
    execution process is fully recorded during the execution of ReCentAutoma.
    
    Because we launched the Playwright MCP Server with the --save-video option,
    a recording of the session is saved in the temporary directory after execution.
    The entire browser operation can be viewed in the saved video file.
    """
    # Initialize LLM instance
    llm = OpenAILlm(
        api_base=_api_base,
        api_key=_api_key,
        configuration=OpenAIConfiguration(model=_model_name),
        timeout=180,
    )

    # Create a temporary directory for Playwright output (videos, screenshots, etc.)
    temp_dir = os.path.realpath(tempfile.mkdtemp())
    print(f"✓ Using temporary directory: {temp_dir}")

    # Connect to Playwright MCP server
    # Note: This requires Node.js and npx to be installed
    playwright_connection = McpServerConnectionStdio(
        name="connection-playwright-stdio",
        command="npx",
        args=[
            "@playwright/mcp@latest",
            f"--output-dir={temp_dir}",
            "--viewport-size=1920x1080",
            "--save-video=1920x1080",
        ],
        request_timeout=60,
    )

    # Register the connection with a dedicated manager
    # This allows isolation from other MCP connections (e.g., CLI, filesystem)
    McpServerConnectionManager.get_instance("browser-use").register_connection(playwright_connection)

    # Establish the connection and verify connection and list available tools
    # Note: registration must be done before calling connect()
    playwright_connection.connect()
    print(f"✓ Connected to Playwright MCP server: {playwright_connection.name}")
    print(f"  Connection status: {playwright_connection.is_connected}")

    # List tools
    tools = playwright_connection.list_tools()
    print(f"✓ Found {len(tools)} available browser tools\n")

    # Create a browser automation agent with Playwright MCP tools
    browser_agent = ReCentAutoma(
        llm=llm,
        tools=tools,
        memory_config=ReCentMemoryConfig(
            llm=llm,
            max_node_size=8,
            max_token_size=1024 * 32,
        ),
        stop_condition=StopCondition(max_iteration=20, max_consecutive_no_tool_selected=1),
        running_options=RunningOptions(debug=True),
    )

    # Use the agent to find recent gold prices on Hong Kong Gold Exchange website
    result = await browser_agent.arun(
        goal=(
            "Find the recent gold prices on Hong Kong Gold Exchange website."
        ),
        guidance=(
            "Do the following steps one by one:\n"
            "1. Navigate to https://hkgx.com.hk/en\n"
            "2. Hover on the 'Market & Data' button to show more button options\n"
            "3. Click the 'History Price' button to access the historical price page\n"
            "4. Since the current date was selected, only need to select the option of RMB-denominated kilo gold\n"
            "5. Click the search button and have a look at the recent gold price trends\n"
            "6. Close the browser and give out a summary of recent gold price trends\n"
        ),
    )

    print("Final Result:\n\n")
    print(result)

    # Close the connection when done
    playwright_connection.close()
    print(f"\n✓ Connection closed: {not playwright_connection.is_connected}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
