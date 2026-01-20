# detect.py - 监控图片变化，并显示第一个 .png 的名称
import os
import time
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
DATA_FILE = "last_images.json"  # 保存上次图片列表


def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def send_alert(first_png):
    title = "🔥 有新的头目出现了"
    content = f"最新刷新头目的图像：**{first_png}**\n\n请立即前往查看 >>\n🔗 [点击查看详情]({URL})"
    try:
        requests.post(
            f"https://sctapi.ftqq.com/{SENDKEY}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        print(f"✅ 已发送提醒：{first_png}")
    except Exception as e:
        print("❌ 推送失败:", e)


def extract_png_urls(driver):
    """提取页面中所有 .png 图片地址"""
    png_urls = []
    try:
        time.sleep(6)  # 等待加载

        # 查找 <img> 标签
        images = driver.find_elements("tag name", "img")
        for img in images:
            src = img.get_attribute("src")
            if src and ".png" in src.lower():
                clean_url = src.split('?')[0].strip()
                if clean_url not in png_urls:
                    png_urls.append(clean_url)

        # 查找 CSS 背景图中的 .png
        if not png_urls:
            all_elems = driver.find_elements("css selector", "*")
            for elem in all_elems:
                bg = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).backgroundImage;", elem)
                if 'png' in bg:
                    import re
                    matches = re.findall(r'url\(["\']?(.+?\.png)["\']?\)', bg)
                    for m in matches:
                        m = m.split('?')[0]
                        if m not in png_urls:
                            png_urls.append(m)

    except Exception as e:
        print("⚠️ 图片提取失败:", e)

    return sorted(png_urls)


def load_last_images():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return []
    return []


def save_images(urls):
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
            # 有变化
            first_png = current_images[0]  # 取第一个完整 URL

            # 提取文件名（如 638.png）
            filename = first_png.split('/')[-1]

            print(f"🔔 检测到图片变化，首个新图为：{filename}")
            send_alert(filename)  # 发微信，只显示文件名
            save_images(current_images)
        else:
            print("✅ 图片无变化")

    except Exception as e:
        print("❌ 错误:", str(e))
    finally:
        if driver:
            driver.quit()
