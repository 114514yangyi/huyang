import base64
import random
import time
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

cookies = [
    {"name": "_uab_collina",
     "value": "171119257405296422620864"},
    {"name": "abtest_env",
     "value": "product"},
    {"name": "zsxq_access_token",
     "value": "F56B8F26-1FF7-D97C-204F-6D953A643298_F23D3E5403214006"},
    {"name": "zsxqsessionid",
     "value": "103c1f2a9e41f468c10360d07bafef8d"}
]

chrome_options = Options()
chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速，某些情况下有用
chrome_options.add_argument("--window-size=1920x1080")  # 指定窗口大小
# chrome_options.add_argument('--proxy-server=http://127.0.0.1:7890')
driver = webdriver.Chrome(service=Service(), options=chrome_options)
driver.get("https://articles.zsxq.com/")
time.sleep(2)
for cookie in cookies:
    driver.add_cookie(cookie)
driver.get("https://articles.zsxq.com/id_jdk4dxd436bm.html")
wait = WebDriverWait(driver, 10)
link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "点击查看答案")))
# 查找页面上所有“点击查看答案”的链接
answer_links = driver.find_elements(By.LINK_TEXT, "点击查看答案")
i = 1
time.sleep(5)
# 依次点击每个链接
for link in answer_links:
    try:
        if i < 54:
            i += 1
            continue
        link.click()
        time.sleep(5)
        window_handles = driver.window_handles
        driver.switch_to.window(window_handles[-1])
        time.sleep(2)
        title = driver.title
        title = title.replace("/", "-")
        # 点击链接
        # 通过执行JavaScript发送DevTools命令来保存PDF
        result = driver.execute_cdp_cmd("Page.printToPDF", {
            "landscape": False
        })
        i = i + 1

        # PDF内容是以base64编码返回的，需要解码并保存到文件
        with open(str(i-1) + "-" + title + ".pdf", "wb") as file:
            file.write(base64.b64decode(result['data']))
        time.sleep(random.uniform(1, 3))
        driver.switch_to.window(window_handles[-1])
        driver.close()
        if len(window_handles) > 1:
            driver.switch_to.window(window_handles[0])
        time.sleep(2)
    except Exception as e:
        print("在点击链接或等待过程中发生了错误:", e)
        # 可以在这里加入额外的错误处理逻辑
# driver.quit()
# time.sleep(200)
