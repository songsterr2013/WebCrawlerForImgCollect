import os
import time
#import pickle
from dotenv import load_dotenv
from util import read_json, url_generator, time_stoper, make_folder, get_batch
from urllib.parse import urljoin
import base64

from seleniumbase import Driver
#from selenium import webdriver
from selenium.webdriver.common.by import By
#from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
#import requests

class WebCrawlerSelenium:
    def __init__(self, base_url, login_url, username, password):
        self.base_url = base_url
        self.login_url = login_url
        self.username = username
        self.password = password
        self.middle_url = "?page="
        self.main_dir_name = "Downloaded_images"
        self.driver = None

        # 一旦實例化就執行
        self._start_browser()

    def _start_browser(self):
        """
        啟動瀏覽器並訪問主頁面。
        """
        print("========== 啟動瀏覽器中... ==========")
        self.driver = Driver(uc=True)

        self.driver.uc_open_with_reconnect(self.base_url, 5)
        print(f"已成功訪問: {self.base_url}")
        time_stoper(1)

    def close_browser(self):
        """
        關閉瀏覽器。
        """
        if self.driver:
            self.driver.quit()
            print("========== 瀏覽器已關閉 ==========")
        else:
            print("瀏覽器未啟動，無需關閉！")

    def login(self):
        """
        模擬登入網站
        """
        print(f"==========Logging in...{self.login_url}==========")
        self.driver.uc_open_with_reconnect(self.login_url, 5)

        # 這邊透過程式點擊重新整理後，CF會顯示失敗，因此一切都只好手動登入，只要突破這一關口後面就暢通無阻
        print("請重新整理，並手動登入，繞過CF")
        time_stoper(10)

        # 等待登入成功
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "user-index"))
        )
        print("登入成功！請觀察頁面上是否顯示在已登入狀態中。")

    def crawl(self, url_provider, loop_times, start_idx):
        """
        爬取圖片 URL 並下載
        """
        # 建立最外圍folder
        make_folder(self.main_dir_name)

        for count, url in enumerate(url_provider):
            loop = count + 1
            current_idx  = count + start_idx
            folder_name = f"{current_idx }_{url.rsplit('/', 1)[-1]}"

            print(f"==========({loop} / {loop_times}) 爬取img url中: {url}==========")

            # 1.基於list中的url進入指定的網址並取得所有圖片的url
            to_download = self.get_all_images(url)

            # 2.基於第1步所取得的所有url進行下載
            to_dl_len = len(to_download)
            self.download_images(img_urls=url_generator(to_download), dir_name=folder_name, loop_times=to_dl_len)

    def get_all_images(self, url:str):
        """
        獲取所有目標img的url，return出一個裝有url的list
        """
        print("==========正在獲取目標底下的所有子url...==========")
        img_urls = []
        self.crawl_img(url=url, img_urls=img_urls)
        print(f"共找到 {len(img_urls)} 張圖片")
        print(img_urls)
        return img_urls

    def crawl_img(self, url:str, img_urls:list, page=1, count=-1):
        """
        基於對html的parse，從頁面中提取所有目標img的url，並檢查是否有下一頁來進行RECUR
        最後在get_all_images中會return出一個結合每一頁的URL list
        """
        count += 1

        print(f'進入目標頁面{url}中... 遞迴次數: {count}')
        self.driver.uc_open_with_reconnect(url, 5)

        # 將最終目標元素的下一項元素設為「是否已加載完成的目標」，可確保整頁已順利加載
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h3.h5.mt-3"))
        )

        # 然後才去獲取IMG URL和下一頁的URL
        photos_list_div = self.driver.find_element(By.CSS_SELECTOR, "div.photos-list.text-center")
        images = photos_list_div.find_elements(By.CSS_SELECTOR, "img[data-src]")
        for img in images:
            img_url = img.get_attribute("data-src")
            if img_url:
                img_urls.append(img_url)

        # 再檢查是否有下一頁的元素
        try:
            page_links  = self.driver.find_elements(By.CSS_SELECTOR, "a.page-link")
            for link in page_links:
                if link.text == "下一頁":
                    page += 1
                    next_page_url = urljoin(url, f"{self.middle_url}{page}")
                    self.crawl_img(url=next_page_url, img_urls=img_urls, page=page, count=count) # RECUR
                    return
        except NoSuchElementException as e:
            print(f"NoSuchElementException: {e}")

        print("已到達尾頁，將跳出RECUR")

    def download_images(self, img_urls, dir_name, loop_times):
        """
        基於dir_name於Downloaded_images中創建子folder
        下載圖片
        """
        # 先創建好子folder
        sub_folder_name = os.path.join(self.main_dir_name, dir_name)
        make_folder(sub_folder_name)

        for idx, img_url in enumerate(img_urls):
            loop = idx + 1
            print(f"==========({loop} / {loop_times}) 下載圖片中: {img_url}==========")
            try:
                self.driver.uc_open_with_reconnect(img_url, 5)

                # 定位IMG的位置
                img_element= self.driver.find_element(By.CSS_SELECTOR, "img")
                # 設定檔案儲存路徑
                img_name = os.path.basename(img_url)
                save_path = os.path.join(self.main_dir_name, dir_name, f"{loop}_{img_name}")
                # 不請求改用JS強行提取
                self.save_image_via_selenium(self.driver, img_element, save_path)
            except Exception as e:
                print(f"下載失敗: {img_url}, 原因: {e}")

    def save_image_via_selenium(self, driver, img_element, save_path):
        # 使用 Selenium 的 execute_script 提取圖片數據
        img_base64 = driver.execute_script("""
            var img = arguments[0];
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').substring(22);  // 去掉 "data:image/png;base64,"
        """, img_element)

        # 將 base64 數據轉為二進制並保存為文件
        with open(save_path, "wb") as file:
            file.write(base64.b64decode(img_base64))
        print(f"下載成功，圖片已保存到: {save_path}")


if __name__ == "__main__":
    load_dotenv()

    # 加載配置
    BASE_URL = os.getenv("BASE_URL")
    LOGIN_URL = os.getenv("LOGIN_URL")
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")

    # parse保存所有url的json檔
    file_name = "urls.json"
    all_urls = read_json(file_name)

    # 每天限爬16份，總共分4天進行
    day = 1
    batch_len, batch_url, batch_start_idx = get_batch(all_urls, batch_number=day)

    # 創建爬蟲實例
    start_time = time.time()

    crawler = WebCrawlerSelenium(base_url=BASE_URL, login_url=LOGIN_URL, username=EMAIL, password=PASSWORD)
    crawler.login()
    crawler.crawl(url_provider=url_generator(batch_url), loop_times=batch_len, start_idx=batch_start_idx)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"程式執行時間: {execution_time:.2f} 秒")

    print("執行結束，按 Ctrl+C 關閉程序或手動關閉瀏覽器。")
    try:
        while True:
            time_stoper(1)
    except KeyboardInterrupt:
        print("程序結束，關閉瀏覽器。")
        crawler.close_browser()

