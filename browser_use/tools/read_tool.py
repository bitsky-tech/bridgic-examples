from bridgic.asl import ASLAutoma, ASLField, graph
from bridgic.core.agentic.tool_specs import AutomaToolSpec

from browser_use.tools.browser.browser_workers import (
    open_page,
    read_content
)


class ReadTool(ASLAutoma):
    """
    阅读技能，可以阅读指定的网页内容，并返回阅读结果

    Args:
        url: 网页链接

    Returns:
        str: 阅读结果
    """

    with graph(
        url=ASLField(type=str, description="网页链接")
    ) as g:
        open = open_page
        read = read_content

        +open >> ~read


read_tool_spec = AutomaToolSpec.from_raw(
    ReadTool,
    tool_name="ReadTool",
    tool_description="Read the content of the given URL",
    tool_parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to read the content from"},
        }
    }
)

########################################################################################################################
# 函数方式
########################################################################################################################

import asyncio


async def read_tool(url: str):
    read_tool = ReadTool()
    result = await read_tool.arun(url=url)
    print(result)


if __name__ == "__main__":
    asyncio.run(read_tool("https://zhidao.baidu.com/question/451140147.html?fr=search&word=%E6%8C%91%E9%80%89%E5%AE%B6%E7%94%A8%E7%94%B5%E8%84%91%E9%94%AE%E7%9B%98%E7%9A%84%E5%BB%BA%E8%AE%AE%E5%92%8C%E6%8A%80%E5%B7%A7"))