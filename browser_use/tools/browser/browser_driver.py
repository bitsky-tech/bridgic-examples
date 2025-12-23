"""
浏览器驱动：封装浏览器自动化操作


playwright>=1.40.0
Pillow>=10.0.0
requests>=2.31.0
trafilatura>=1.6.0
"""
import io
import re
import json
import asyncio
import random
import typing as t

from PIL import Image
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import trafilatura
import readability


class BrowserDriver:
    """
    浏览器驱动：封装浏览器自动化操作（基于 Playwright）
    
    支持的操作：
    - 打开网页
    - 截图
    - 点击元素
    - 滚动页面
    - 等待页面加载
    - 提取针对于咨询文章的主要内容
    
    反爬措施：
    - 随机 User-Agent
    - 随机延迟
    - 禁用自动化检测标志
    - 模拟人类行为
    """
    
    # 常见的 User-Agent 列表
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        """
        初始化浏览器驱动
        
        Args:
            headless: 是否无头模式
            browser_type: 浏览器类型（"chromium", "firefox", "webkit"）
        """
        self.headless = headless
        self.browser_type = browser_type

        self.playwright = None
        self.browser: t.Optional[Browser] = None
        self.context: t.Optional[BrowserContext] = None
        self.page: t.Optional[Page] = None
    
    async def _init_driver(self):
        """初始化浏览器驱动"""
        try:
            self.playwright = await async_playwright().start()
            
            # 根据浏览器类型启动对应的浏览器
            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',  # 禁用自动化检测
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                    ]
                )
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"不支持的浏览器类型: {self.browser_type}")
            
            # 创建浏览器上下文，设置反爬措施
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(self.USER_AGENTS),
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                # 设置额外的反检测参数
                extra_http_headers={
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            # 添加反检测脚本
            await self.context.add_init_script("""
                // 覆盖 navigator.webdriver 属性
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 覆盖 chrome 对象
                window.chrome = {
                    runtime: {}
                };
                
                // 覆盖 permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // 覆盖 plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // 覆盖 languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)
            
            # 创建新页面
            self.page = await self.context.new_page()
            
        except Exception as e:
            raise RuntimeError(f"初始化浏览器驱动失败: {e}")
    
    @classmethod
    async def create(cls, headless: bool = True, browser_type: str = "chromium"):
        """异步创建浏览器驱动实例"""
        instance = cls(headless=headless, browser_type=browser_type)
        await instance._init_driver()
        return instance
    
    async def _random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """随机延迟，模拟人类行为"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def open_url(self, url: str, timeout: int = 60000, retry: int = 2) -> bool:
        """
        打开网页
        
        Args:
            url: 网页 URL
            timeout: 超时时间（毫秒），默认 60 秒
            retry: 重试次数，默认 2 次
            
        Returns:
            是否成功打开
        """
        if not self.page:
            raise RuntimeError("浏览器页面未初始化")
        
        # 重试机制
        for attempt in range(retry + 1):
            try:
                # 随机延迟，模拟人类行为
                await self._random_delay(0.5, 1.5)
                
                # 访问网页，使用更宽松的等待条件
                # 'domcontentloaded' 比 'networkidle' 更宽松，只等待 DOM 加载完成
                # 'load' 等待页面和资源加载完成
                # 'networkidle' 等待网络空闲（可能太严格导致超时）
                try:
                    await self.page.goto(
                        url, 
                        wait_until='load',  # 先尝试 'load'，比 'networkidle' 更宽松
                        timeout=timeout
                    )
                except Exception as e:
                    # 如果 'load' 也超时，尝试更宽松的 'domcontentloaded'
                    if 'timeout' in str(e).lower() or 'Timeout' in str(e):
                        print(f"使用 'load' 超时，尝试使用 'domcontentloaded'...")
                        await self.page.goto(
                            url,
                            wait_until='domcontentloaded',  # 最宽松的条件
                            timeout=timeout
                        )
                    else:
                        raise
                
                # 确保页面在顶部（避免动态内容导致的位置偏移）
                await self.scroll_to_top()
                return True
            except Exception as e:
                error_msg = str(e)
                is_timeout = 'timeout' in error_msg.lower() or 'Timeout' in error_msg
                
                if attempt < retry:
                    wait_time = (attempt + 1) * 2
                    print(f"打开网页失败（尝试 {attempt + 1}/{retry + 1}）: {error_msg}")
                    print(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"打开网页失败（已重试 {retry} 次）: {error_msg}")
                    if is_timeout:
                        print(f"提示: 网站加载较慢，可以尝试：")
                        print(f"  1. 增加超时时间（当前: {timeout}ms）")
                        print(f"  2. 检查网络连接")
                        print(f"  3. 网站可能有反爬虫机制")
                    return False
        
        return False

    async def get_page_content(self) -> str:
        """
        获取页面内容
        """
        if not self.page:
            raise RuntimeError("浏览器页面未初始化")
        
        origin_content = await self.page.content()
        content = re.sub(r'<script[^>]*>.*?</script>', '', origin_content, flags=re.DOTALL)
        return content
    
    async def input_text(self, css_selector: str, text: str, human_like: bool = True) -> bool:
        """
        输入文本（模拟人类输入行为）
        
        Args:
            css_selector: CSS Selector 表达式
            text: 要输入的文本
            human_like: 是否启用拟人化输入（逐字符输入，随机延迟）
        """
        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        if css_selector.startswith("```"):
            css_selector = css_selector.strip("```")
            css_selector = css_selector.strip("css")
            css_selector = css_selector.strip()
        
        try:
            locator = self.page.locator(f"css={css_selector}")
            
            # 先点击元素，聚焦
            await locator.click()
            await self._random_delay(0.1, 0.3)  # 点击后短暂延迟
            
            # 尝试查找真正的输入元素（可能在容器内部）
            # 先尝试直接使用定位器
            input_locator = None
            
            # 检查定位的元素是否是可编辑元素
            try:
                # 尝试获取元素的标签名
                tag_name = await locator.evaluate("el => el.tagName.toLowerCase()")
                is_editable_eval = await locator.evaluate("el => el.contentEditable === 'true'")
                is_editable = tag_name in ['input', 'textarea'] or is_editable_eval
                
                if is_editable:
                    input_locator = locator
                else:
                    # 如果不是可编辑元素，尝试在容器内查找输入框
                    # 查找 input, textarea 或 contenteditable 元素
                    inner_input = locator.locator("input, textarea, [contenteditable='true']").first
                    if await inner_input.count() > 0:
                        input_locator = inner_input
                    else:
                        # 如果找不到，尝试使用 JavaScript 设置文本
                        # 先尝试设置 value 属性（适用于 input）
                        try:
                            # 使用 evaluate 传递参数，避免特殊字符问题
                            await locator.evaluate("""
                                (el, text) => {
                                    el.value = '';
                                    el.value = text;
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            """, text)
                            await self._random_delay(0.2, 0.4)
                            return True
                        except:
                            # 如果 value 设置失败，尝试设置 textContent 或 innerText（适用于 contenteditable div）
                            try:
                                await locator.evaluate("""
                                    (el, text) => {
                                        el.textContent = '';
                                        el.textContent = text;
                                        el.dispatchEvent(new Event('input', { bubbles: true }));
                                        el.dispatchEvent(new Event('change', { bubbles: true }));
                                    }
                                """, text)
                                await self._random_delay(0.2, 0.4)
                                return True
                            except:
                                raise RuntimeError("无法找到可编辑的输入元素，也无法通过 JavaScript 设置文本")
            except Exception as e:
                # 如果检查失败，尝试直接查找内部输入框
                try:
                    inner_input = locator.locator("input, textarea, [contenteditable='true']").first
                    if await inner_input.count() > 0:
                        input_locator = inner_input
                    else:
                        raise RuntimeError(f"无法找到可编辑的输入元素: {e}")
                except:
                    raise RuntimeError(f"无法找到可编辑的输入元素: {e}")
            
            # 如果找到了输入定位器，使用标准方法输入
            if input_locator:
                # 清空输入框
                try:
                    await input_locator.clear()
                except:
                    # 如果 clear 失败，尝试使用 JavaScript 清空
                    await input_locator.evaluate("el => { if (el.tagName.toLowerCase() === 'input' || el.tagName.toLowerCase() === 'textarea') { el.value = ''; } else { el.textContent = ''; } }")
                await self._random_delay(0.1, 0.2)
                
                if human_like:
                    # 拟人化输入：逐字符输入，模拟真实打字速度
                    for i, char in enumerate(text):
                        # 输入单个字符
                        await input_locator.type(char, delay=random.uniform(50, 150))  # 每个字符延迟 50-150ms
                        
                        # 偶尔模拟停顿（比如思考、检查输入）
                        if i > 0 and i % random.randint(5, 12) == 0:
                            # 每输入 5-12 个字符后，随机停顿一下
                            await self._random_delay(0.2, 0.5)
                        
                        # 小概率模拟输入错误和修正（5% 概率）
                        if random.random() < 0.05 and i < len(text) - 1:
                            # 输入一个错误字符
                            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                            await input_locator.type(wrong_char, delay=random.uniform(50, 100))
                            await self._random_delay(0.1, 0.2)
                            # 删除错误字符
                            await input_locator.press('Backspace')
                            await self._random_delay(0.1, 0.2)
                else:
                    # 快速输入模式（直接填充）
                    await input_locator.fill(text)
                
                # 输入完成后短暂延迟，模拟检查输入内容
                await self._random_delay(0.2, 0.4)
            
            return True
        except Exception as e:
            raise RuntimeError(f"输入文本失败: {e}")
    
    async def scroll_to_top(self):
        """滚动到页面顶部"""
        if not self.page:
            return
        
        try:
            # 使用 JavaScript 直接滚动到顶部，更可靠
            await self.page.evaluate("window.scrollTo(0, 0)")
            # 等待滚动完成
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"滚动到顶部失败: {e}")
    
    async def scroll_to_bottom(self):
        """滚动到页面底部"""
        if not self.page:
            return
        
        try:
            # 使用 JavaScript 直接滚动到底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # 等待滚动完成
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"滚动到底部失败: {e}")
    
    async def screenshot(self, save_path: t.Optional[str] = None, full_page: bool = True, ensure_top: bool = True) -> Image.Image:
        """
        截图当前页面
        
        Args:
            save_path: 保存路径（可选）
            full_page: 是否截取整个页面
                - True: 截取整个网页（包括需要滚动才能看到的部分）
                - False: 只截取浏览器当前显示的可视区域
            ensure_top: 截图前是否确保页面在顶部（默认 True）
                       设置为 True 可以避免页面位置不对导致截图内容错位
            
        Returns:
            PIL Image 对象
        """
        if not self.page:
            raise RuntimeError("浏览器页面未初始化")
        
        try:
            # 如果设置了 ensure_top，先滚动到顶部并等待稳定
            if ensure_top:
                await self.scroll_to_top()
                await asyncio.sleep(0.5)  # 等待页面稳定
            
            # 截图
            screenshot_bytes = await self.page.screenshot(
                type='png',
                full_page=full_page  # 控制是否截取整个页面
            )
            
            # 转换为 PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # 如果指定了保存路径，保存图片
            if save_path:
                image.save(save_path)
            
            return image
        except Exception as e:
            raise RuntimeError(f"截图失败: {e}")
    
    async def click_element(self, css_selector: str, timeout: int = 30000) -> bool:
        """
        点击页面元素
        
        Args:
            css_selector: CSS Selector 表达式
            timeout: 超时时间（毫秒），默认 30 秒
            
        Returns:
            是否成功点击
        """
        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        if css_selector.startswith("```"):
            css_selector = css_selector.strip("```")
            css_selector = css_selector.strip("css")
            css_selector = css_selector.strip()
        
        try:
            locator = self.page.locator(f"css={css_selector}")
            
            # 先等待元素可见
            await locator.wait_for(state="visible", timeout=timeout)
            
            # 滚动到元素位置，确保元素在视口内
            await locator.scroll_into_view_if_needed()
            
            # 等待一小段时间，确保元素稳定（避免动画或动态内容干扰）
            await asyncio.sleep(0.5)
            
            # 执行点击操作（Playwright 的 click 会自动等待元素可交互）
            await locator.click(timeout=timeout)
            return True
        except Exception as e:
            raise RuntimeError(f"点击元素失败: {e}")

    async def extract_element(self, css_selector: str, timeout: int = 15000) -> str:
        """
        提取元素内容
        
        Args:
            css_selector: CSS 选择器
            timeout: 超时时间（毫秒），默认 15 秒
        """
        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        if css_selector.startswith("```"):
            css_selector = css_selector.strip("```")
            css_selector = css_selector.strip("css")
            css_selector = css_selector.strip()
        
        # 清理选择器（移除可能的 markdown 代码块标记）
        css_selector = css_selector.strip()
        
        
        try:
            # 先等待页面稳定（给动态内容一些加载时间）
            await asyncio.sleep(2)
            
            locator = self.page.locator(f"css={css_selector}")
            
            # 先检查元素是否存在（使用 count）
            count = await locator.count()
            if count == 0:
                print(f"警告: 元素 {css_selector} 在页面中不存在（count=0）")
                print(f"      当前页面 URL: {self.page.url}")
                print(f"      尝试等待元素出现...")
                # 等待元素出现
                try:
                    await locator.wait_for(state="visible", timeout=timeout)
                    count = await locator.count()
                    print(f"      等待后元素数量: {count}")
                except Exception as wait_error:
                    print(f"      等待元素出现失败: {wait_error}")
                    # 检查是否有相似的选择器
                    print(f"      返回空字符串以继续运行...")
                    return ""
            
            # 尝试获取元素内容
            try:
                # 使用更长的超时时间
                content = await locator.first.inner_html(timeout=10000)
                print(f"[Extract] 成功提取元素内容，长度: {len(content)} 字符")
                return content
            except Exception as html_error:
                print(f"警告: 无法获取元素 {css_selector} 的内容: {html_error}")
                # 尝试使用 text() 作为备选
                try:
                    text_content = await locator.first.inner_text(timeout=5000)
                    print(f"      使用文本内容作为备选，长度: {len(text_content)} 字符")
                    return text_content
                except:
                    print(f"      返回空字符串以继续运行...")
                    return ""
        except Exception as e:
            # demo 性质：如果提取失败，返回空字符串而不是抛出异常
            print(f"警告: 提取元素 {css_selector} 失败: {e}")
            print(f"      当前页面 URL: {self.page.url}")
            print(f"      返回空字符串以继续运行...")
            return ""
    
    async def scroll(self, direction: str = "down", pixels: int = 500):
        """
        滚动页面
        
        Args:
            direction: 滚动方向（"up" 或 "down"）
            pixels: 滚动像素数
        """
        if not self.page:
            return
        
        try:
            # 使用鼠标滚轮滚动
            if direction == "down":
                await self.page.mouse.wheel(0, pixels)
            else:
                await self.page.mouse.wheel(0, -pixels)
            
            # 滚动后随机延迟
            await self._random_delay(0.3, 0.8)
        except Exception as e:
            print(f"滚动失败: {e}")
    
    async def get_page_size(self) -> t.Tuple[int, int]:
        """
        获取页面尺寸（实际内容尺寸，不仅仅是视口）
        
        Returns:
            (width, height)
        """
        if not self.page:
            return (1920, 1080)
        
        try:
            # 获取视口大小
            viewport = self.page.viewport_size
            if viewport:
                # 获取实际页面内容尺寸
                content_size = await self.page.evaluate("""
                    () => {
                        return {
                            width: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth),
                            height: Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)
                        };
                    }
                """)
                return (content_size['width'], content_size['height'])
            return (1920, 1080)
        except Exception as e:
            print(f"获取页面尺寸失败: {e}")
            return (1920, 1080)
    
    def get_current_url(self) -> str:
        """获取当前页面 URL"""
        if not self.page:
            return ""
        
        try:
            return self.page.url
        except Exception as e:
            print(f"获取当前 URL 失败: {e}")
            return ""
    
    async def extract_content(self, include_comments: bool = False) -> t.Dict[str, str]:
        """
        提取网页主要内容（基于 Readability 算法）
        
        使用 trafilatura 或 readability 库从 HTML 中提取主要内容，
        自动过滤掉导航栏、侧边栏、广告等无关内容。
        
        Args:
            include_comments: 是否包含评论内容（默认 False）
            
        Returns:
            包含以下字段的字典：
            - title: 页面标题
            - content: 主要内容文本
            - text: 纯文本内容（去除 HTML 标签）
            - html: 提取的 HTML 内容（如果可用）
            - author: 作者（如果可提取）
            - date: 发布日期（如果可提取）
            - url: 页面 URL
        """
        if not self.page:
            raise RuntimeError("浏览器页面未初始化")
        
        # 获取页面 HTML 内容
        html_content = await self.page.content()
        url = self.page.url
        
        result = {
            'title': '',
            'content': '',
            'text': '',
            'html': '',
            'author': '',
            'date': '',
            'url': url
        }
        
        try:
            # 方法1: 使用 JSON 格式，然后解析
            extracted_json = trafilatura.extract(
                html_content,
                include_comments=include_comments,
                include_links=False,  # 不包含链接文本
                include_images=False,  # 不包含图片描述
                output_format='json',  # 返回 JSON 字符串
                url=url
            )
            
            if extracted_json:
                import json
                extracted = json.loads(extracted_json)
                result['title'] = extracted.get('title', '')
                result['content'] = extracted.get('text', '')
                result['text'] = extracted.get('text', '')
                result['html'] = extracted.get('html', '')
                result['author'] = extracted.get('author', '')
                result['date'] = extracted.get('date', '')
            
            # 方法2: 使用 readability 库提取内容
            # doc = readability.Document(html_content)
            # result['title'] = doc.short_title()
            # result['content'] = doc.summary()
            # result['text'] = doc.text()
            # result['html'] = doc.content()
            # result['author'] = doc.author()
            # result['date'] = doc.date()
                
        except Exception as e:
            print(f"使用 trafilatura 提取内容失败: {e}")
            # 如果 trafilatura 失败，尝试使用备用方法
            try:
                # 备用方法：只提取文本
                extracted_text = trafilatura.extract(
                    html_content,
                    output_format='txt',
                    url=url
                )
                if extracted_text:
                    result['content'] = extracted_text
                    result['text'] = extracted_text
            except Exception as e2:
                print(f"备用提取方法也失败: {e2}")
        
        return result
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"关闭浏览器失败: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None


########################################################################################################################
# 测试代码
########################################################################################################################


async def main():
    print("=" * 60)
    print("浏览器驱动测试")
    print("=" * 60)
    
    # 创建浏览器驱动（可以设置 headless=False 来查看浏览器操作）
    driver = await BrowserDriver.create(headless=True, browser_type="chromium")
    
    try:
        # 测试打开网页
        # test_url = "https://pages.quark.cn/r/quark-newspaper-pc/detail?aid=16926344029992235069&uc_param_str=dnfrpfbivessbtbmnilauputogpintnwmtsvcppcprsnnnchmiccgiodaacameosipbd&entry_from=nav_dailynews&back_url=https%3A%2F%2Fpages.quark.cn%2Fr%2Fquark-newspaper-pc%2Fchannel%3Fentry_from%3Dnav_dailynews&from_page=channel&recoid=12623841822171332118&from_pos=subject_card"
        # test_url = "https://baijiahao.baidu.com/s?id=1850930114445897182"
        # test_url = "https://news.qq.com/rain/a/20251208A05DX300"
        test_url = "https://zhidao.baidu.com/question/1188958045666314379.html?fr=search&word=%E9%80%89%E8%B4%AD%E6%B4%97%E8%A1%A3%E6%9C%BA%E6%97%B6%2C%E4%B8%80%E8%88%AC%E8%A6%81%E6%B3%A8%E6%84%8F%E5%93%AA%E4%BA%9B%E6%96%B9%E9%9D%A2%3F"
        print(f"\n1. 正在打开网页: {test_url}")
        # 增加超时时间到 60 秒，并启用重试
        success = await driver.open_url(test_url, timeout=60000, retry=2)
        
        if success:
            print("✓ 网页打开成功")
            
            # 获取当前 URL
            current_url = driver.get_current_url()
            print(f"✓ 当前 URL: {current_url}")
            
            # # 获取页面尺寸
            # width, height = await driver.get_page_size()
            # print(f"✓ 页面尺寸: {width} x {height}")
            
            # # 测试截图（整个页面）
            # print("\n2. 正在截图（整个页面）...")
            # screenshot_full = await driver.screenshot(save_path="test_screenshot_full.png", full_page=True)
            # print(f"✓ 全页面截图成功，尺寸: {screenshot_full.size}")
            # print(f"✓ 截图已保存到: test_screenshot_full.png")
            
            # # 测试截图（仅可视区域）
            # print("\n3. 正在截图（仅可视区域）...")
            # screenshot_viewport = await driver.screenshot(save_path="test_screenshot_viewport.png", full_page=False)
            # print(f"✓ 可视区域截图成功，尺寸: {screenshot_viewport.size}")
            # print(f"✓ 截图已保存到: test_screenshot_viewport.png")
            
            # # 测试滚动
            # print("\n4. 测试滚动...")
            # await driver.scroll("down", 500)
            # print("✓ 向下滚动成功")
            # await asyncio.sleep(1)
            # await driver.scroll("up", 300)
            # print("✓ 向上滚动成功")
            
            # 测试提取主要内容
            print("\n5. 测试提取网页主要内容...")
            try:
                content_result = await driver.extract_content()
                print(f"✓ 提取成功")
                print(f"  - 标题: {content_result.get('title', 'N/A')[:100]}")
                print(f"  - 内容长度: {len(content_result.get('content', ''))} 字符")
                print(f"  - 作者: {content_result.get('author', 'N/A')}")
                print(f"  - 日期: {content_result.get('date', 'N/A')}")
                if content_result.get('content'):
                    preview = {
                        'title': content_result.get('title', 'N/A'),
                        'content': content_result.get('content', ''),
                        'author': content_result.get('author', 'N/A'),
                        'date': content_result.get('date', 'N/A'),
                    }
                    print(f"  - 内容预览: {json.dumps(preview, indent=4, ensure_ascii=False)}")
            except Exception as e:
                print(f"✗ 提取内容失败: {e}")
            
            # 等待一下，观察效果
            print("\n等待 3 秒后关闭浏览器...")
            await asyncio.sleep(3)
        else:
            print("✗ 网页打开失败")
    
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭浏览器
        print("\n6. 正在关闭浏览器...")
        await driver.close()
        print("✓ 浏览器已关闭")
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
