from DrissionPage import ChromiumPage, ChromiumOptions
from pathlib import Path
import json
import time

# --- 配置路径 (保持不变) ---
BASE_DIR = Path(r'D:\mine\save\program\python\mine_web\backend\services\spider\platforms\xhs')
USER_DATA_DIR = BASE_DIR / 'user_data'
options = ChromiumOptions()
options.set_paths(user_data_path=USER_DATA_DIR)
page = ChromiumPage(options)

TARGET_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/search/notes'
SCROLL_TIMES = 10          # 最多滚动次数（备用上限）
TARGET_COUNT = 50          # 🔢 目标帖子数量，达到后自动停止

try:
    print(f"🎧 开始监听: {TARGET_API}")
    page.listen.start(TARGET_API)

    url = "https://www.xiaohongshu.com/search_result?keyword=%25E5%2593%25B2%25E5%25AD%25A6%25E4%25B8%2593%25E4%25B8%259A%25E5%25A5%25BD%25E5%2590%2597&source=web_explore_feed"
    page.get(url)

    print("🧹 清空之前缓存的请求包...")
    page.listen.clear()

    # 筛选操作
    filter_btn = page.ele('text=筛选')
    filter_btn.hover()
    most_comment_btn = page.wait.ele_displayed('text=最多评论', timeout=10)
    most_comment_btn.click()
    page.wait(1)
    if page.ele('text=收起', timeout=3):
        page.ele('text=收起').click()

    print("✅ 筛选完成，等待首次 API 响应...")
    packet = page.listen.wait(timeout=15)

    if not packet:
        print("⚠️ 未捕获到目标请求")
        page.listen.stop()
        input("\n按回车关闭...")
        exit()

    # 处理响应的函数
    def process_response(packet, page_num):
        response_data = packet.response.body
        if isinstance(response_data, dict):
            json_data = response_data
        elif isinstance(response_data, bytes):
            json_data = json.loads(response_data.decode('utf-8'))
        else:
            json_data = json.loads(response_data)

        notes = json_data.get('data', {}).get('items', [])
        print(f"📦 第 {page_num} 页 | 获取 {len(notes)} 条笔记")
        return notes

    all_notes = []
    notes = process_response(packet, 1)
    all_notes.extend(notes)

    # 检查首次是否已达标
    if len(all_notes) >= TARGET_COUNT:
        print(f"\n🎯 已达到目标数量 {TARGET_COUNT} 条，停止采集")
        all_notes = all_notes[:TARGET_COUNT]  # 截取精确数量
    else:
        # 开始滚动获取后续数据
        for i in range(SCROLL_TIMES):
            print(f"\n⬇️ 执行第 {i + 1} 次滚动...")
            page.listen.clear()          # 清空缓存，只等新的请求
            page.scroll.to_bottom()      # 滚动到底部
            time.sleep(2)                # 等待请求发出并完成

            # 等待新的响应包
            new_packet = page.listen.wait(timeout=3)
            if new_packet:
                notes = process_response(new_packet, i + 2)
                all_notes.extend(notes)
                # ✅ 检查是否已达到目标数量
                if len(all_notes) >= TARGET_COUNT:
                    print(f"\n🎯 已达到目标数量 {TARGET_COUNT} 条，停止滚动")
                    all_notes = all_notes[:TARGET_COUNT]  # 截取精确数量
                    break
            else:
                print("⚠️ 未捕获到新响应，跳过本次滚动")

    print(f"\n✅ 采集完成，实际获取 {len(all_notes)} 条笔记（目标 {TARGET_COUNT}）")
    page.listen.stop()
    input("\n按回车关闭...")

except Exception as e:
    print(f"❌ 发生错误: {e}")
    import traceback
    traceback.print_exc()
    input("\n按回车关闭...")