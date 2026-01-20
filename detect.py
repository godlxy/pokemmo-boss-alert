# detect.py - 监控 monster-alpha 页面中的 .png 图片变化
import os
import time
import hashlib
import json
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# === 配置 ===
URL = "https://pokemmo.lanbizi.com/monster-alpha"
SENDKEY = os.getenv("SENDKEY")
DATA_FILE = "last_images.json"  # 保存上次抓到的图片列表


def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def send_alert():
    title = "🔥 有新的头目出现了"
    content = "α头目列表中的图片已更新，请立即查看 >>\n\n🔗 [点击查看详情]({})".format(URL)
    try:
        requests.post(
            f"https://sctapi.ftqq.com/{SENDKEY}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        print("✅ 提醒已发送")
    except Exception as e:
        print("❌ 推送失败:", e)


def extract_png_urls(driver):
    """提取页面中所有 .png 图片地址"""
    png_urls = []
    try:
        # 等待页面加载
        time.sleep(6)

        # 查找所有 img 标签
        images = driver.find_elements("tag name", "img")
        for img in images:
            src = img.get_attribute("src")
            if src and ".png" in src.lower():
                # 只保留关键部分，避免时间戳等参数干扰
                clean_url = src.split('?')[0].strip()
                if clean_url not in png_urls:
                    png_urls.append(clean_url)

        # 备用：查找背景图或 CSS 中的 png
        if not png_urls:
            all_elements = driver.find_elements("css selector", "*")
            for elem in all_elements:
                bg = driver.execute_script("""
                    return window.getComputedStyle(arguments[0]).backgroundImage;
                """, elem)
                if 'png' in bg:
                    import re
                    matches = re.findall(r'url\(["\']?(.+?\.png)["\']?\)', bg)
                    for m in matches:
                        m = m.split('?')[0]
                        if m not in png_urls:
                            png_urls.append(m)

    except Exception as e:
        print("⚠️ 图片提取出错:", e)

    return sorted(png_urls)  # 排序确保一致性


def load_last_images():
    """读取上次保存的图片列表"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return []
    return []


def save_images(urls):
    """保存当前图片列表"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)


# 主逻辑
if __name__ == "__main__":
    driver = None
    try:
        print(f"[{datetime.now()}] 正在检查图片更新...")
        driver = get_driver()
        driver.get(URL)

        current_images = extract_png_urls(driver)
        last_images = load_last_images()

        if not current_images:
            print("🟡 未检测到任何 .png 图片")
        elif set(current_images) != set(last_images):
            # 有新增、删除或修改
            print(f"🔔 图片列表变化！原:{len(last_images)} 现:{len(current_images)}")
            send_alert()
            save_images(current_images)
        else:
            print("✅ 图片无变化")

    except Exception as e:
        print("❌ 错误:", str(e))
    finally:
        if driver:
            driver.quit()
