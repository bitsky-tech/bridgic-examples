from bridgic.asl import ASLAutoma, ASLField, graph, Data
from bridgic.core.automa.args import From
from bridgic.core.agentic.tool_specs import AutomaToolSpec, FunctionToolSpec

from browser_use.tools.browser.browser_workers import (
    open_page,
    input_text,
    find_element_1,
    find_element_2,
    find_element_3,
    click_element,
    get_page_content,
    extract_element,
    find_search_results
)


# class SearchTool(ASLAutoma):
#     """
#     搜索，可以进入指定的搜索引擎网页，输入用户 query 让浏览器执行检索

#     Args:
#         url: 搜索引擎网站链接
#         query: 用户搜索的问题

#     Returns:
#         None
#     """

#     with graph(
#         url=ASLField(type=str, description="搜索引擎网站链接"),
#         query=ASLField(type=str, description="用户搜索的问题")
#     ) as g:
#         open = open_page  # 打开浏览器
#         find_search = find_element_1 *Data(target=From("no_exit", "找到搜索栏"))  # 查找搜索框
#         input_search = input_text  # 输入搜索关键词
#         find_search_button = find_element_2 *Data(html_content=From("open"), target=From("no_exit", "找到搜索按钮"))  # 查找搜索按钮
#         click_search_button = click_element  # 点击搜索按钮

#         +open >> find_search >> input_search >> find_search_button >> click_search_button
    

# class GetSearchResultsTool(ASLAutoma):
#     """
#     获取搜索结果，可以获取搜索结果页面中的所有搜索结果

#     Args:
#         None

#     Returns:
#         list[str]: 搜索结果
#     """
#     with graph as g: 
#         current_page = get_page_content
#         find_results = find_element_3 *Data(target=From("no_exit", "找到所有搜索结果主要在哪个标签下"))
#         results_html = extract_element
#         results = find_search_results *Data(target=From("no_exit", "提取 html 中的所有搜索结果"))   

#         +current_page >> find_results >> results_html >> results


# search_tool_spec = AutomaToolSpec.from_raw(
#     SearchTool,
#     tool_name="SearchTool",
#     tool_description="Search the given query on the given URL",
#     tool_parameters={
#         "type": "object",
#         "properties": {
#             "url": {"type": "string", "description": "The URL to search the query on"},
#             "query": {"type": "string", "description": "The query to search for"}
#         }
#     }
# )


# get_search_results_tool_spec = AutomaToolSpec.from_raw(
#     GetSearchResultsTool,
#     tool_name="GetSearchResultsTool",
#     tool_description="Get the search results from the given URL",
#     tool_parameters={
#         "type": "object",
#         "properties": {}
#     }
# )


########################################################################################################################
# 函数方式
########################################################################################################################
import asyncio


async def search_tool(inputs_dict: dict):
    """
    Execute a search operation on the given URL by entering the query and clicking the search button.
    This tool only performs the search action and navigates to the search results page.

    Parameters:
    ----------
    url: str
        The URL of the search engine website (e.g., https://zhidao.baidu.com/)
    query: str
        The search query/keywords to search for

    Returns:
    -------
    str: "success" if the search operation completed successfully
    """
    url = inputs_dict["url"]
    query = inputs_dict["query"]
    await open_page(url)
    html_content = await get_page_content()
    css_selector = find_element_1("找到搜索栏", html_content)
    await input_text(css_selector, query)
    await asyncio.sleep(1)
    html_content = await get_page_content()
    css_selector = find_element_2("找到搜索按钮", html_content)
    await click_element(css_selector)
    return "success"
    


async def get_search_results_tool(inputs):
    """
    Extract and return the search results from the current search results page.
    This tool should be used AFTER search_tool has been executed successfully and 

    Note: This tool requires that you are already on a search results page.
    If you haven't executed a search yet, use search_tool first.

    Returns:
    -------
    list[dict]: A list of search result dictionaries, each containing title, url, and date fields
    """
    html_content = await get_page_content()
    css_selector = find_element_3("找到所有搜索结果主要在哪个标签下", html_content)
    search_results_html = await extract_element(css_selector)
    search_results = find_search_results("提取 html 中的第一个搜索结果", search_results_html)
    return search_results


search_tool_spec = FunctionToolSpec.from_raw(search_tool)
get_search_results_tool_spec = FunctionToolSpec.from_raw(get_search_results_tool)


########################################################################################################################
# 测试
########################################################################################################################
# import time

# async def test_search_tool():
#     await search_tool(url="https://zhidao.baidu.com/", query="挑选洗衣机时要注意一些什么？")
#     results = await get_search_results_tool()
#     print(f'成功获取搜索结果: {results}')


# if __name__ == "__main__":
#     asyncio.run(search_tool("https://zhidao.baidu.com/", "挑选洗衣机时要注意一些什么？"))
    



