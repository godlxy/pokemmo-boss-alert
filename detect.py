# detect.py - 只要数据更新，就提醒，并显示第一个alpha名称
import os
import time
import hashlib
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# === 配置 ===
URL = "https://pokemmo.lanbizi.com/monster-alpha"
SENDKEY = os.getenv("SENDKEY")
DATA_FILE = "last_hash.txt"  # 用于记录上次内容指纹

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def send_alert(first_alpha):
    title = "🔥 有新的头目出现了"
    content = f"最新刷新的α头目：**{first_alpha}**\n\n请立即前往查看 >>\n🔗 [点击查看详情]({URL})"
    try:
        requests.post(
            f"https://sctapi.ftqq.com/{SENDKEY}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        print(f"✅ 已发送提醒：{first_alpha}")
    except Exception as e:
        print("❌ 推送失败:", e)

def extract_first_alpha(driver):
    """提取页面上第一个α头目的名字"""
    try:
        time.sleep(5)
        # 尝试获取所有行（常见结构）
        rows = driver.find_elements("css selector", "table tbody tr", "tr.row", ".list-item")
        for row in rows:
            text = row.text.strip()
            if not text:
                continue
            if any(k in text for k in ["No.", "序号", "名称", "暂无数据"]):
                continue  # 跳过表头或空提示
            # 分割文本，取第二个字段为名称（假设格式：No 名称 等级 地图...）
            parts = text.split()
            if len(parts) >= 2:
                name = parts[1].strip()
                if len(name) <= 10:  # 防止取到乱码
                    return name
    except:
        pass

    # 备用方案：从全文找第一个含关键词的宝可梦名
    try:
        body = driver.find_element("tag name", "body")
        all_text = body.text
        lines = all_text.split('\n')
        for line in lines:
            if any(kw in line for kw in ["头目", "BOSS", "刷新", "挑战"]) and len(line) > 10:
                # 提取中文词或英文单词（可能是宝可梦名）
                import re
                match = re.search(r"[\u4e00-\u9fa5a-zA-Z]{2,10}", line)
                if match:
                    word = match.group()
                    # 排除常见动词
                    if word not in ["刷新", "出现", "挑战", "地址", "坐标"]:
                        return word
    except:
        pass

    return "未知宝可梦"

def get_page_fingerprint(driver):
    """生成页面内容指纹（MD5哈希）"""
    try:
        ele = driver.find_element("css selector", "table, .content, body")
        text = ele.text.strip()[:1000]  # 取前1000字符
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    except:
        return hashlib.md5(b"empty").hexdigest()

def load_last_hash():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return f.read().strip()
    return ""

def save_hash(h):
    with open(DATA_FILE, 'w') as f:
        f.write(h)

# 主逻辑
if __name__ == "__main__":
    driver = None
    try:
        print(f"[{datetime.now()}] 正在检查头目更新...")
        driver = get_driver()
        driver.get(URL)

        # 获取当前页面指纹
        current_hash = get_page_fingerprint(driver)
        last_hash = load_last_hash()

        if current_hash != last_hash:
            # 页面有变化 → 提取第一个alpha并提醒
            first_alpha = extract_first_alpha(driver)
            print(f"🔔 检测到更新，首个头目：{first_alpha}")
            send_alert(first_alpha)
            save_hash(current_hash)  # 更新指纹
        else:
            print("✅ 无变化，跳过")

    except Exception as e:
        print("❌ 错误:", str(e))
    finally:
        if driver:
            driver.quit()
