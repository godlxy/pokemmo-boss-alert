# detect.py - PoKéMMO 头目报点监控脚本
import os
import time
import hashlib
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# === 配置区 ===
URL = "https://pokemmo.lanbizi.com/monster-alpha"
SENDKEY = os.getenv("SENDKEY")  # 从 GitHub Secrets 获取
DATA_FILE = "last_hash.txt"

# 浏览器设置
def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# 发送微信提醒
def send_wx(title, content):
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ 微信推送成功")
    except Exception as e:
        print("❌ 推送失败:", e)

# 读取上次哈希值
def load_last_hash():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return f.read().strip()
    return ""

# 保存当前哈希值
def save_current_hash(h):
    with open(DATA_FILE, 'w') as f:
        f.write(h)

# 主程序开始
if __name__ == "__main__":
    driver = None
    try:
        print(f"[{datetime.now()}] 开始检查页面...")
        driver = create_driver()
        driver.get(URL)
        time.sleep(6)  # 等待JS加载完成

        # 尝试提取关键区域（根据实际结构调整）
        try:
            # 方法1：尝试选择常见消息容器
            messages = driver.find_elements("css selector", ".message-item, .chat-content, li")
            if messages:
                text_content = "\n".join([m.text.strip() for m in messages if m.text.strip()])
            else:
                # 方法2：退化为全文本
                body = driver.find_element("tag name", "body")
                text_content = body.text
        except:
            body = driver.find_element("tag name", "body")
            text_content = body.text

        # 取前1000字符做指纹（避免太大）
        sample = text_content[:1000]
        current_hash = hashlib.md5(sample.encode('utf-8')).hexdigest()

        last_hash = load_last_hash()

        if current_hash != last_hash:
            print("🚨 检测到变化，发送提醒！")
            save_current_hash(current_hash)
            send_wx(
                "🔔 蓝鼻子头目有新报点！",
                f"页面内容已更新，请立即查看 >\n\n🔗 {URL}\n\n🕒 {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            print("✅ 无变化，跳过推送")

    except Exception as e:
        print("❌ 执行出错:", str(e))
        send_wx("⚠️ 监控脚本报错", str(e)[:500])
    finally:
        if driver:
            driver.quit()
