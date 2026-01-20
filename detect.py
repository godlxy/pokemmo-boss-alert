# detect.py - 极简模式：页面内容变了吗？变了就提醒
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
DATA_FILE = "last_content_hash.txt"

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def send_alert():
    title = "🔔 头目已出现！"
    content = f"α头目列表已更新，请立即查看 >>\n\n{URL}"
    try:
        requests.post(
            f"https://sctapi.ftqq.com/{SENDKEY}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        print("✅ 提醒已发送")
    except Exception as e:
        print("❌ 发送失败:", e)

def get_page_fingerprint(driver):
    # 等待页面加载
    time.sleep(5)
    try:
        # 尝试获取主要容器
        ele = driver.find_element("css selector", "table, .list, .content, body")
        text = ele.text.strip()
    except:
        # 备用：直接取 body
        text = driver.find_element("tag name", "body").text.strip()
    # 返回前1000字符的哈希
    return hashlib.md5(text[:1000].encode('utf-8')).hexdigest()

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
        driver = get_driver()
        driver.get(URL)
        print(f"[{datetime.now()}] 正在加载页面...")

        current_hash = get_page_fingerprint(driver)
        last_hash = load_last_hash()

        if current_hash != last_hash:
            print("🔥 检测到更新！发送提醒")
            send_alert()
            save_hash(current_hash)
        else:
            print("✅ 无变化，跳过")

    except Exception as e:
        print("❌ 错误:", e)
    finally:
        if driver:
            driver.quit()
