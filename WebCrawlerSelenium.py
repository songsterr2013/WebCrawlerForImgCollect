from util import url_generator, time_stoper, make_folder
import os
import base64
from urllib.parse import urljoin

from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class WebCrawlerSelenium:
    def __init__(self, base_url, login_url, username, password):
        self.base_url = base_url
        self.login_url = login_url
        self.username = username
        self.password = password
        self.middle_url = "?page=" # 將頻繁使用作為url拼接
        self.main_dir_name = "Downloaded_images" # 創建folder用
        self.driver = None

        # 一旦實例化就執行
        self._start_browser()

    def _start_browser(self):
        """
        for啟動瀏覽器用
        1. 初始化一個基於 undetected-chromedriver 的瀏覽器實例。
        2. 首先打開主頁面 URL，確保driver有成功運作。
        """
        print("========== 啟動瀏覽器中... ==========")
        self.driver = Driver(uc=True)

        self.driver.uc_open_with_reconnect(self.base_url, 5)
        print(f"已成功訪問: {self.base_url}")
        time_stoper(1)

    def close_browser(self):
        """
        for關閉瀏覽器用
        """
        if self.driver:
            self.driver.quit()
            print("========== 瀏覽器已關閉 ==========")
        else:
            print("瀏覽器未啟動，無需關閉！")

    def login(self):
        """
        for登入網站用
        1. 進入登入頁面
        2. 在time_stoper(10)期間手動對網頁進行重新整理，並自行輸入登入資訊，點擊CF驗證
        3. 手動登入過程能讓該網站的CF認為你是真實使用者
        4. 隨後在WebDriverWait會檢查是否有user-index的元素，如有，即已成功登入
        """
        print(f"==========Logging in...{self.login_url}==========")
        self.driver.uc_open_with_reconnect(self.login_url, 5)

        # 這邊透過程式點擊重新整理後，CF會顯示失敗，因此一切都只好手動登入，只要突破這一關口後面就暢通無阻
        print("請重新整理，並手動登入，繞過CF")
        time_stoper(10)

        # 等待登入成功
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "user-index"))
        )
        print("登入成功！請觀察頁面上是否顯示在已登入狀態中。")

    def crawl(self, url_provider, loop_times:int, start_idx:int):
        """
        一系列的爬蟲動作都寫在這裡了
        :param url_provider: 傳進來的應該要是生成器
        :param loop_times: 這是len(list)，用於顯示爬蟲進度用
        :param start_idx: 確保在分批執行時傳入正確的batch index，供後面創建sub folder命名用
        1. 先建立最外圍folder
        2. folder_name供後面下載圖片時，創建folder和指明下載路徑時使用
        3. to_download，基於list中的url進入指定的網址並取得所有圖片的url，return出list
        4. 該list將放到self.download_images()中進行圖片下載
        """
        # 建立最外圍folder
        make_folder(self.main_dir_name)

        for count, url in enumerate(url_provider):
            loop = count + 1
            current_idx  = count + start_idx
            folder_name = f"{current_idx }_{url.rsplit('/', 1)[-1]}"
            print(f"==========({loop} / {loop_times}) 爬取img url中: {url}", "==========")

            to_download = self.get_all_images(url)
            to_dl_len = len(to_download)
            self.download_images(img_urls=url_generator(to_download), dir_name=folder_name, loop_times=to_dl_len)

    def get_all_images(self, url:str):
        """
        獲取所有目標img的url
        :param url: 爬取目標url
        :returns: 裝有目標url底下的所有子url的list
        1. 創建img_urls，供self.crawl_img存放所有url
        2. self.crawl_img執行後會把結果存放在創建img_urls
        """
        print("==========正在獲取目標底下的所有子url...==========")
        img_urls = []
        self.crawl_img(url=url, img_urls=img_urls)
        print(f"共找到 {len(img_urls)} 張圖片")
        return img_urls

    def crawl_img(self, url:str, img_urls:list, page=1, count=-1):
        """
        基於對html的parse，從頁面中提取所有目標img的url，並檢查是否有下一頁來進行RECUR
        :param url: 目標url
        :param img_urls: 存放子url的list
        :param page: 作為url拼接使用，獲取下一頁
        :param count: 作為recur次數記錄用，0代表最外圍那一層
        :return: 跳出recur用
        1. 進入目標url頁面
        2. 將最終目標元素的下一項元素設為「是否已加載完成的目標」，可確保整頁已順利加載
        3. 然後去獲取IMG URL存到list中
        4. 檢查是否有下一頁的元素，如有就recur
        """
        count += 1

        print(f'進入目標頁面{url}中... 遞迴次數: {count}')
        self.driver.uc_open_with_reconnect(url, 5)

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "footer.pt-2.mt-2.pb-2.border-top"))
        )

        photos_list_div = self.driver.find_element(By.CSS_SELECTOR, "div.photos-list.text-center")
        images = photos_list_div.find_elements(By.CSS_SELECTOR, "img[data-src]")
        for img in images:
            img_url = img.get_attribute("data-src")
            if img_url:
                img_urls.append(img_url)

        try:
            page_links  = self.driver.find_elements(By.CSS_SELECTOR, "a.page-link")
            for link in page_links:
                if link.text == "下一頁":
                    print(f'{link.text}')
                    page += 1
                    next_page_url = urljoin(url, f"{self.middle_url}{page}")
                    self.crawl_img(url=next_page_url, img_urls=img_urls, page=page, count=count) # RECUR
                    return

        except NoSuchElementException as e:
            print(f"NoSuchElementException: {e}")

        print("已到達尾頁，將跳出RECUR")

    # 考慮到既然canvas可行，這一個func似乎可以歸納到crawl_img中，邊下載，邊換頁，省得selenium每次都要重新加載img頁面
    # 如果可行，執行速度將大幅提升
    def download_images(self, img_urls, dir_name:str, loop_times:int):
        """
        下載圖片
        :param img_urls: 目標子url
        :param dir_name: 子url所屬folder的檔名
        :param loop_times: 這是len(list)，用於顯示爬蟲進度用
        1. 基於dir_name於Downloaded_images中創建子folder
        2. for中直接進入img url頁面
        3. 取得img的位置
        4. 設定檔案儲存路徑
        5. 在save_image_via_selenium中，不利用請求改用JS canvas提取
        """
        # 先創建好子folder
        sub_folder_name = os.path.join(self.main_dir_name, dir_name)
        make_folder(sub_folder_name)

        for idx, img_url in enumerate(img_urls):
            loop = idx + 1
            print(f"==========({loop} / {loop_times}) 下載圖片中: {img_url}", "==========")
            try:
                self.driver.uc_open_with_reconnect(img_url, 5)

                img_element= self.driver.find_element(By.CSS_SELECTOR, "img")

                img_name = os.path.basename(img_url)
                save_path = os.path.join(self.main_dir_name, dir_name, f"{loop}_{img_name}")

                self.save_image_via_selenium(self.driver, img_element, save_path)
            except Exception as e:
                print(f"下載失敗: {img_url}, 原因: {e}")

    @staticmethod
    def save_image_via_selenium(driver, img_element, save_path):
        """
        利用JavaScript 中的canvas來繪製圖像
        :param driver: 利用selenium中的execute_script方法執行js syntax
        :param img_element: 待下載img的元素
        :param save_path: img存放路徑
        1. 從 canvas 提取圖像數據
        2. Base64 解碼為二進制
        3. 前題是，圖片未設置CORS安全策略，如有，照片tainted將無法繪製
        4. 目前不確定是縮製格式是否設定太大所導致img size比起網站上的要大出數倍，還是提取到被瀏覽器壓縮前的origin img
        """
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