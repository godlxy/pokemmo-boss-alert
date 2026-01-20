# detect.py - 显示倒数第二个 .png 图片的文件名
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
DATA_FILE = "last_images.json"


def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def send_alert(penultimate_png):
    title = "🔥 有新的头目出现了"
    content = f"倒数第二个头目图像：**{penultimate_png}**\n\n请立即前往查看 >>\n🔗 [点击查看详情]({URL})"
    try:
        requests.post(
            f"https://sctapi.ftqq.com/{SENDKEY}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        print(f"✅ 已发送提醒：{penultimate_png}")
    except Exception as e:
        print("❌ 推送失败:", e)


def extract_png_urls(driver):
    """提取所有 .png 图片 URL"""
    png_urls = []
    try:
        time.sleep(6)

        # 提取 <img> 标签中的 .png
        images = driver.find_elements("tag name", "img")
        for img in images:
            src = img.get_attribute("src")
            if src and ".png" in src.lower():
                clean_url = src.split('?')[0].strip()
                if clean_url not in png_urls:
                    png_urls.append(clean_url)

        # 提取 CSS 背景图中的 .png
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

    return png_urls  # 保持原始顺序（通常是 DOM 出现顺序）


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

        if len(current_images) < 2:
            print("🟡 图片少于2个，跳过提醒")
        elif set(current_images) != set(last_images):
            # 有变化 → 取倒数第二个
            if len(current_images) >= 2:
                penultimate_url = current_images[-2]  # 倒数第二个
                filename = penultimate_url.split('/')[-1]  # 只取文件名
                print(f"🔔 检测到变化，倒数第二个图为：{filename}")
                send_alert(filename)
                save_images(current_images)
            else:
                print("🟡 不足两个图片，无法获取倒数第二个")
        else:
            print("✅ 图片无变化")

    except Exception as e:
        print("❌ 错误:", str(e))
    finally:
        if driver:
            driver.quit()
