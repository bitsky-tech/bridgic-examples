from typing import Optional
from pydantic import BaseModel
import asyncio

from bridgic.core.model.protocols import PydanticModel
from bridgic.core.model.types import Role, Message

from browser_use.tools.browser.browser_driver import BrowserDriver
from browser_use.tools.llm_tool import llm_worker


# 全局浏览器驱动实例（单例模式）
_browser_driver: Optional[BrowserDriver] = None


async def _get_browser_driver() -> BrowserDriver:
    """获取或创建浏览器驱动实例（单例模式）"""
    global _browser_driver
    if _browser_driver is None:
        _browser_driver = await BrowserDriver.create(headless=False, browser_type="chromium")
    return _browser_driver


async def get_page_content() -> str:
    """
    获取页面内容
    """
    driver = await _get_browser_driver()
    return await driver.get_page_content()


async def open_page(url: str) -> str:
    """
    打开网页，等待加载完成，并返回加载完成后的 HTML
    
    Args:
        url: 要打开的网页 URL
        
    Returns:
        加载完成后的 HTML 内容（字符串）
        
    Raises:
        RuntimeError: 如果打开网页失败或浏览器页面未初始化
    """
    if isinstance(url, dict):
        url = url["url"]
    driver = await _get_browser_driver()
    success = await driver.open_url(url, timeout=60000, retry=2)
    if not success:
        raise RuntimeError(f"打开网页失败: {url}")
    await asyncio.sleep(1)
    return await driver.get_page_content()


def find_element_1(html_content: str, target: str) -> str:
    """
    查找元素
    """
    response = llm_worker(
        model="gpt-4o-mini",
        messages=[
            Message.from_text(
                text=f"You are a helpful assistant that can find elements in HTML content."
                    f"You will be given a target and HTML content."
                    f"You need to find the element that matches the target."
                    f"**Only return the CSS Selector of the element, no other text.**"
                    f"**The CSS Selector should be a valid CSS Selector expression.**",
                role=Role.SYSTEM
            ),
            Message.from_text(
                text=f"Target: {target}\nHTML Content: {html_content}",
                role=Role.USER
            )
        ]
    )
    css_selector = response.message.content
    return css_selector


def find_element_2(html_content: str, target: str) -> str:
    """
    查找元素
    """
    response = llm_worker(
        model="gpt-4o-mini",
        messages=[
            Message.from_text(
                text=f"You are a helpful assistant that can find elements in HTML content."
                    f"You will be given a target and HTML content."
                    f"You need to find the element that matches the target."
                    f"**Only return the CSS Selector of the element, no other text.**"
                    f"**The CSS Selector should be a valid CSS Selector expression.**",
                role=Role.SYSTEM
            ),
            Message.from_text(
                text=f"Target: {target}\nHTML Content: {html_content}",
                role=Role.USER
            )
        ]
    )
    css_selector = response.message.content
    return css_selector


def find_element_3(html_content: str, target: str) -> str:
    """
    查找元素
    """
    response = llm_worker(
        model="gpt-4o-mini",
        messages=[
            Message.from_text(
                text=f"You are a helpful assistant that can find elements in HTML content."
                    f"You will be given a target and HTML content."
                    f"You need to find the element that matches the target."
                    f"**Only return the CSS Selector of the element, no other text.**"
                    f"**The CSS Selector should be a valid CSS Selector expression.**",
                role=Role.SYSTEM
            ),
            Message.from_text(
                text=f"Target: {target}\nHTML Content: {html_content}",
                role=Role.USER
            )
        ]
    )
    css_selector = response.message.content
    return css_selector


async def extract_element(css_selector: str) -> str:
    """
    提取元素内容
    """
    driver = await _get_browser_driver()
    content = await driver.extract_element(css_selector)
    return content



async def input_text(css_selector: str, query: str) -> str:
    """
    输入文本
    """
    driver = await _get_browser_driver()
    await driver.input_text(css_selector, query)
    return css_selector


async def click_element(css_selector: str) -> str:
    """
    点击元素
    
    此函数可以在同步和异步环境中使用。
    如果在异步环境中调用，会自动在线程池中执行以避免 greenlet 错误。
    """
    driver = await _get_browser_driver()
    await driver.click_element(css_selector)
    await asyncio.sleep(3)


def find_search_results(html_content: str, target: str) -> str:
    """
    查找搜索结果内容
    """
    class SearchResult(BaseModel):
        model_config = {
            "extra": "forbid",
            "json_schema_extra": {
                "required": ["title", "url", "date"],
                "additionalProperties": False,
            }
        }
        title: str
        url: str
        date: str

    # class SearchResults(BaseModel):
    #     model_config = {
    #         "extra": "forbid",
    #         "json_schema_extra": {
    #             "required": ["results"],
    #             "additionalProperties": False,
    #         }
    #     }
    #     results: List[SearchResult]

    response = llm_worker(
        model="gpt-4o-mini",
        messages=[
            Message.from_text(
                text=f"You are a helpful assistant that can extract content in HTML content."
                    f"You will be given a HTML content."
                    f"You need to extract the target from the HTML content."
                    f"**Only return the search results, no other text.**",
                role=Role.SYSTEM
            ),
            Message.from_text(
                text=f"Target: {target}\nHTML Content: {html_content}",
                role=Role.USER
            )
        ],
        type="structure_output",
        constraint=PydanticModel(model=SearchResult),
        timeout=600,
        max_tokens=4096
    )
    return response


async def read_content(html_content: str) -> str:
    """
    读取网页内容
    """
    driver = await _get_browser_driver()
    content = await driver.extract_content()
    return content


########################################################################################################################
# 测试
########################################################################################################################
import time


async def main():
    st = time.time()

    print(f'{"=" * 20} 打开网页 {"=" * 20}')
    await open_page("https://zhidao.baidu.com/")
    html_content = await get_page_content()
    print(f'成功打开网页: https://zhidao.baidu.com/\n')

    print(f'{"=" * 20} 找到搜索栏 {"=" * 20}')
    css_selector = find_element_1("找到搜索栏", html_content)
    print(f'成功找到搜索栏: {css_selector}\n')

    print(f'{"=" * 20} 输入文本 {"=" * 20}')
    await input_text(css_selector, "挑选洗衣机时要注意一些什么？")
    print(f'成功输入文本: 挑选洗衣机时要注意一些什么？\n')

    print(f'{"=" * 20} 点击搜索按钮 {"=" * 20}')
    css_selector = find_element_2("找到搜索按钮", html_content)
    await click_element(css_selector)
    print(f'成功点击搜索按钮: {css_selector}\n')
    await asyncio.sleep(5)

    print(f'{"=" * 20} 获取搜索结果 {"=" * 20}')
    html_content = await get_page_content()
    print(f'成功获取搜索结果页面: {html_content[:200]}\n')
    css_selector = find_element_3("找到所有搜索结果主要在哪个标签下", html_content)
    print(f'成功找到搜索结果主要在哪个标签下: {css_selector}\n')
    search_results_html = await extract_element(css_selector)
    print(f'成功提取搜索结果: {search_results_html[:200]}\n')
    search_results = find_search_results("提取 html 中的所有搜索结果", search_results_html)
    print(type(search_results))
    print(f'成功找到搜索结果: {search_results}\n')

    print(f'总耗时: {time.time() - st} 秒\n')
    while input("是否退出？(y/n)") == "y":
        exit()


if __name__ == "__main__":
    asyncio.run(main())