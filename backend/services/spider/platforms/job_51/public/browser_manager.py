from DrissionPage import ChromiumOptions, ChromiumPage
from DrissionPage.common import Actions
import re
import time
import json
import random
from typing import List, Tuple, Dict, Any, Optional


class BrowserSessionManager :
    """
    自动处理滑块验证
    """
    def __init__(self, user_agent: Optional[str] = None):
        """
        初始化反爬解决器 (强制有头模式)
        :param user_agent: 自定义 UA，默认使用内置的高仿 UA
        """
        self.page: Optional[ChromiumPage] = None
        # 默认 UA，模拟最新 Chrome
        self.default_ua = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

    def setup_page(self) -> ChromiumPage:
        """配置并启动浏览器 (固定为有头模式)"""
        if self.page and not self.page.closed:
            return self.page

        co = ChromiumOptions()

        # === 核心防检测参数 ===
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--disable-extensions')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-infobars')

        co.set_pref('page_load_strategy', 'eager')
        co.set_user_agent(self.default_ua)

        # 启动浏览器 (可见窗口)
        self.page = ChromiumPage(co)

        # 注入 JS 隐藏自动化特征
        self.page.run_js("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.navigator.chrome = { runtime: {} };
        """)
        return self.page

    def close(self):
        """关闭浏览器"""
        try:
            # 直接尝试关闭页面，如果页面已关闭，DrissionPage 会处理好
            if self.page:
                self.page.quit()
        except Exception as e:
            # 忽略所有可能的错误，例如页面已经关闭
            pass
        finally:
            # 无论是否成功，都清理实例变量
            self.page = None
            self.driver = None # 如果您的类中有 self.driver，也要清理

    def __enter__(self):
        self.setup_page()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def generate_fast_start_track(distance: int, steps: int = 18,
                                  power: float = 2.6) -> List[Tuple[int, int]]:
        """生成含高初速度特征的滑动轨迹 (保持不变)"""
        track = []
        random_initial_factor = 0.15 + random.uniform(-0.03, 0.07)  # 12% + (-2% to 5%)
        initial_displacement = max(1, int(distance * random_initial_factor))
        track.append((initial_displacement, random.randint(-1, 1)))

        remaining_distance = distance - initial_displacement
        remaining_steps = steps - 1

        if remaining_distance <= 0 or remaining_steps <= 0:
            if distance > initial_displacement:
                track.append((distance - initial_displacement, 0))
            return track

        last_segment_pos = initial_displacement
        effective_remaining_distance = int(remaining_distance * 0.98)

        for i in range(1, remaining_steps + 1):
            t = i / remaining_steps
            current_pos_in_remainder = round((t ** power) * effective_remaining_distance)
            absolute_pos = initial_displacement + current_pos_in_remainder
            absolute_pos = min(absolute_pos, initial_displacement + effective_remaining_distance)

            step_size = absolute_pos - last_segment_pos
            if step_size <= 0:
                continue

            max_y_jitter = min(2, int(step_size / 4) + 1)
            step_y = random.randint(-max_y_jitter, max_y_jitter)
            track.append((step_size, step_y))
            last_segment_pos = absolute_pos

        current_total = sum(step[0] for step in track)
        if current_total < distance:
            track.append((distance - current_total, random.randint(-1, 1)))
            current_total = distance

        if random.random() < 0.85:
            overshoot = random.randint(1, 2)
            track.append((-overshoot, random.randint(-2, 2)))
            current_total -= overshoot
            if random.random() < 0.3 and current_total < distance:
                track.append((1, random.randint(-1, 1)))

        final_pos = sum(step[0] for step in track)
        if abs(final_pos - distance) > 2:
            track.append((distance - final_pos, 0))

        return track

    def _is_json_response_loaded(self) -> Tuple[bool, str, Optional[Any]]:
        """检查当前页面是否已加载 JSON 响应"""
        if not self.page:
            return False, "Page not initialized", None

        page_html = self.page.html
        if '<pre>' in page_html and '</pre>' in page_html:
            try:
                start_idx = page_html.find('<pre>') + len('<pre>')
                end_idx = page_html.find('</pre>')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = page_html[start_idx:end_idx]
                    data = json.loads(json_str)
                    return True, "JSON 响应加载成功", data
                else:
                    return False, "未在 <pre> 标签中找到闭合标签", None
            except json.JSONDecodeError as e:
                return False, f"JSON 解析失败: {e}", None
            except Exception as e:
                return False, f"处理错误: {e}", None
        else:
            return False, "页面未包含 <pre> 标签", None

    def solve_and_get_data(self, url: str, max_retries=2) -> Dict[str, Any]:
        """
        核心方法：访问 URL -> 解决滑块 -> 获取 JSON 数据
        (有头模式下，您可以亲眼看到滑块移动)
        """
        if not self.page:
            self.setup_page()

        for attempt in range(1, max_retries + 1):
            try:
                print(f"\n🔄 尝试访问并验证 {attempt}/{max_retries}")
                print(f"   URL: {url[:60]}...")

                self.page.get(url)
                time.sleep(2)  # 等待页面初始加载

                # 1. 检测并处理滑块
                slider_found = True
                try:
                    # 有头模式下，如果滑块出现，您能直接看到
                    slider = self.page.wait.ele_displayed('#nc_1_n1z', timeout=8)
                except:
                    slider_found = False
                    print("ℹ️  未发现滑块，可能无需验证或已自动通过")

                if slider_found:
                    print("✓ 滑块元素已就绪，开始模拟滑动...")
                    container = self.page.ele('#nc_1_n1t')
                    if not container:
                        print("⚠ 未找到滑块轨道容器，重试...")
                        time.sleep(1)
                        continue

                    distance = container.rect.size[0]
                    if distance < 50:
                        print(f"⚠ 轨道宽度异常：{distance}px")
                        time.sleep(1.5)
                        continue

                    print(f"📏 轨道宽度：{distance}px")

                    # 生成轨迹
                    track = self.generate_fast_start_track(distance, steps=18, power=2.6)

                    # 执行滑动 (有头模式下这里会看到鼠标移动)
                    actions = Actions(self.page)
                    actions.hold(slider)
                    for x_offset, y_offset in track:
                        actions.move(x_offset, y_offset)
                    actions.release()

                    actual_end = sum(step[0] for step in track)
                    print(f"✓ 滑动完成 | 目标：{distance}px | 实际：{actual_end}px")

                    # 滑动后稍微多等一会，让服务器验证
                    time.sleep(1)

                    # 2. 等待 JSON 加载
                print("⏳ 等待数据加载...")
                max_wait_time = 15
                elapsed = 0
                json_check_interval = 0.5

                while elapsed < max_wait_time:
                    time.sleep(json_check_interval)
                    is_loaded, message, data = self._is_json_response_loaded()

                    if is_loaded:
                        print(f"✅ 验证成功！数据已获取。")
                        return {'success': True, 'data': data}

                    elapsed += json_check_interval

                print(f"❌ 验证失败：超时未收到 JSON。")
                if attempt < max_retries:
                    print("   -> 准备重试...")
                    time.sleep(random.uniform(2.0, 3.0))
                    continue

                return {'success': False, 'data': None}

            except Exception as e:
                print(f"❌ 发生异常 (尝试{attempt}): {type(e).__name__}: {str(e)[:100]}")
                if attempt == max_retries:
                    return {'success': False, 'data': None}
                time.sleep(random.uniform(1.5, 2.5))

        return {'success': False, 'data': None}

    def extract_json_from_pre(self, html_content: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        从 HTML 字符串中提取 <pre> 标签内的 JSON 内容
        :param html_content: 完整的 HTML 字符串
        :return: (成功标志, JSON数据字典, 消息)
        """
        if not html_content:
            return False, None, "HTML 内容为空"

        # 使用正则表达式查找 <pre> 和 </pre> 之间的内容
        # re.DOTALL 确保匹配跨越多行的内容
        match = re.search(r'<pre>(.*?)</pre>', html_content, re.DOTALL)

        if not match:
            return False, None, "未在 HTML 中找到 <pre> 标签"

        json_str = match.group(1).strip()

        if not json_str:
            return False, None, "<pre> 标签内内容为空"

        try:
            data = json.loads(json_str)
            return True, data, "JSON 提取成功"
        except json.JSONDecodeError as e:
            return False, None, f"JSON 解析失败: {str(e)}"
        except Exception as e:
            return False, None, f"提取过程发生未知错误: {str(e)}"

    def extract_json_from_page(self, page) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        直接从 DrissionPage 对象中提取 <pre> 标签内的 JSON
        :param page: DrissionPage 页面对象
        :return: (成功标志, JSON数据字典, 消息)
        """
        if not page:
            return False, None, "页面对象为空"

        return self.extract_json_from_pre(page.html)