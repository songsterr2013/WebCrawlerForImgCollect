import os
import pickle
from dotenv import load_dotenv
from util import read_json, url_generator, time_stoper, make_folder
from urllib.parse import urljoin

from seleniumbase import Driver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import requests

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
        #page_source = self.driver.page_source
        #print(page_source)
        #exit()
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
        print("==========Logging in...==========")

        self.driver.uc_open_with_reconnect(self.login_url, 5)
        print(f"已成功訪問: {self.login_url}")

        # 這邊透過程式點擊重新整理後，CF會顯示失敗，因此一切都只好手動登入，只要突破這一關口後面就暢通無阻
        print("請重新整理，並手動登入，繞過CF")
        time_stoper(10)

        '''
        # 程式點擊CF人類認證
        self.driver.uc_gui_click_captcha()
        print(f"手動對頁面進行captcha點擊中: {self.login_url}")
        time_stoper(5)

        # 填寫用戶名和密碼
        print("填寫email中...")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        ).send_keys(self.username)
        time_stoper(1)
        print("填寫密碼中...")
        self.driver.find_element(By.NAME, "password").send_keys(self.password)
        time_stoper(5)

        # 按下登入按鈕 (但無論是模擬真實使用者點擊或是用JS執行點擊登入按鈕都會失敗)
        login_button = self.driver.find_element(By.CSS_SELECTOR, 'button.btn.btn-primary[type="submit"]')
        self.driver.execute_script("arguments[0].click();", login_button)
        #self.action.move_to_element(login_button).click().perform()
        time_stoper(3)
        '''

        # 等待登入成功
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "user-index"))
        )
        print("登入成功！請觀察頁面上是否顯示在已登入狀態中。")

    def crawl(self, url_provider, loop_times):
        """
        爬取圖片 URL 並下載
        """
        # 建立最外圍folder
        make_folder(self.main_dir_name)

        for count, url in enumerate(url_provider):
            time_stoper(1)
            loop = count + 1
            folder_name = f"{loop}_{url.rsplit('/', 1)[-1]}"

            print(f"==========({loop} / {loop_times}) 爬取: {url}==========")

            # 1.基於list中的url進入指定的網址並取得所有圖片的url
            to_download = self.get_all_images(url)

            # 2.基於第1步所取得的所有url進行下載
            self.download_images(img_urls=url_generator(to_download), dir_name=folder_name)

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

    def download_images(self, img_urls, dir_name):
        """
        基於dir_name於Downloaded_images中創建子folder
        下載圖片
        """
        sub_folder_name = os.path.join(self.main_dir_name, dir_name)
        make_folder(sub_folder_name)

        for idx, img_url in enumerate(img_urls):
            try:
                self.driver.uc_open_with_reconnect(img_url, 5)

                response = requests.get(img_url, stream=True)
                response.raise_for_status()

                img_name = os.path.basename(img_url)
                save_path = os.path.join(self.main_dir_name, dir_name, f"{idx + 1}_{img_name}")
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"圖片已保存: {save_path}")
            except Exception as e:
                print(f"下載失敗: {img_url}, 原因: {e}")


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
    all_urls_len = len(all_urls)

    # 創建爬蟲實例
    crawler = WebCrawlerSelenium(base_url=BASE_URL, login_url=LOGIN_URL, username=EMAIL, password=PASSWORD)
    crawler.login()
    crawler.crawl(url_provider=all_urls, loop_times=all_urls_len)
    print("執行結束，按 Ctrl+C 關閉程序或手動關閉瀏覽器。")
    try:
        while True:
            time_stoper(1)
    except KeyboardInterrupt:
        print("程序結束，關閉瀏覽器。")
        crawler.close_browser()


    # 開始爬取圖片
    #crawler.crawl(url_provider=all_urls, loop_times=all_urls_len)