# detect.py - 页面有更新就提醒
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
DATA_FILE = "last_hash.txt"

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def send_alert():
    title = "🔥 有新的头目出现了"
    content = "α头目列表已更新，请立即查看 >>\n\n🔗 [点击查看详情]({})".format(URL)
    try:
        requests.post(
            f"https://sctapi.ftqq.com/{SENDKEY}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        print("✅ 提醒已发送")
    except Exception as e:
        print("❌ 推送失败:", e)

def get_page_fingerprint(driver):
    """生成页面内容的哈希指纹"""
    try:
        time.sleep(5)
        # 尝试获取主要容器内容
        ele = driver.find_element("css selector", "table, .content, .list, body")
        text = ele.text.strip()[:1500]  # 截取前1500字符
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    except:
        return hashlib.md5(b"error_or_empty").hexdigest()

def load_last_hash():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return ""

def save_hash(h):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(h)

# 主逻辑
if __name__ == "__main__":
    driver = None
    try:
        print(f"[{datetime.now()}] 正在检查头目更新...")
        driver = get_driver()
        driver.get(URL)

        current_hash = get_page_fingerprint(driver)
        last_hash = load_last_hash()

        if current_hash != last_hash:
            print("🔔 检测到页面更新，发送提醒")
            send_alert()
            save_hash(current_hash)
        else:
            print("✅ 无变化，跳过")

    except Exception as e:
        print("❌ 错误:", str(e))
    finally:
        if driver:
            driver.quit()
