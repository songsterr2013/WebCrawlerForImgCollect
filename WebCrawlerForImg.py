import os
from dotenv import load_dotenv
from util import read_json, url_generator, time_stoper, make_folder
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import cloudscraper

class WebCrawlerForImg:
    def __init__(self, base_url, headers=None, login_url=None, username=None, password=None):
        self.base_url = base_url
        self.headers = headers
        self.session = cloudscraper.create_scraper()

        if login_url and username and password:
            self.login_url = login_url
            self.username = username
            self.password = password
            self._login()

    def _login(self):
        """
        模擬登入網站
        """
        print("Logging in...")

        payload = {
            "username": f"{self.username}",
            "password": f"{self.password}"
        }

        # 第一次先進首頁，目前觀察出現403的情況頗高，但一旦只要出現200，往後爬蟲一路暢通無阻
        response = self.session.get(self.base_url)
        print('進入首頁中...', '請求狀態:', response.status_code)
        time_stoper(2)

        # 進入登入頁面
        response = self.session.get(self.login_url, headers=self.headers)
        print('進入登入頁面中...', '請求狀態:', response.status_code)
        time_stoper(2)

        pass


    def crawl(self, url_provider, loop_times):
        """
        主要爬取的動作都寫在這邊
        基於util中的url_generator生成器，對json進行parse後所取得的url，然後進行爬蟲
        """
        # 第一次先進首頁，目前觀察出現403的情況頗高，但一旦只要出現200，往後爬蟲一路暢通無阻
        response = self.session.get(self.base_url)
        print('進入首頁中...', '請求狀態:', response.status_code)

        for count, url in enumerate(url_provider):
            time_stoper(2) # 隨機暫停器
            loop = count + 1
            print(f"==========({loop} / {loop_times}) 爬取: {url}", '==========')

            # 1.基於list中的url進入指定的網址並取得所有圖片的url
            to_download = self.crawl_img(url)

            # 2.建立最外圍folder
            folder_name = 'Downloaded_images'
            make_folder(folder_name)

            # 3.基於第1步所取得的所有url進行下載
            self.download_images(img_urls=to_download, loop=loop, dir_name=folder_name)

    def crawl_img(self, url):
        """
        基於對html的parse，提取所有目標img的url，最後return出一個list
        """
        response = self.session.get(url, headers=self.headers)
        print(f'進入目標頁面中...', '請求狀態:', response.status_code)

        soup = BeautifulSoup(response.text, 'html.parser')
        div_blocks = soup.find_all("div", class_="album-photo my-2")

        img_urls = []
        for div in div_blocks:
            img_tag = div.find("img", {"data-src": True})
            if img_tag:
                img_urls.append(img_tag["data-src"])

        return img_urls

    def download_images(self, img_urls:list, loop, dir_name):
        """
        對img_urls中的url一個一個access並下載保存到本地
        """
        img_urls_len = len(img_urls)

        # 在主folder中建立子folder
        batch_folder_name = f"{str(loop)}_{dir_name}"
        batch_folder_path = os.path.join(dir_name, batch_folder_name)
        make_folder(batch_folder_path)

        for count, img_url in enumerate(img_urls):
            time_stoper(2)
            new_count = count+1

            print(f'正在處理當前頁面的第 {new_count} / {img_urls_len} 張圖片')

            try:
                # 獲取圖片內容
                print(f"正在下載圖片: {img_url}")
                response = self.session.get(img_url, headers=self.headers, stream=True)  # 使用 stream 提升大文件處理效率
                print('圖片連結請求成功!:', response.status_code)  # 確保請求成功

                # 保存圖片文件名
                img_name = os.path.basename(img_url)
                img_name =  f"{str(new_count)}_{img_name}"
                save_path = os.path.join(batch_folder_path, img_name)

                # 將圖片寫入文件
                with open(save_path, "wb") as img_file:
                    for chunk in response.iter_content(1024):
                        img_file.write(chunk)

                print(f"圖片已保存: {save_path}")

            except Exception as e:
                print(f"下載失敗: {img_url}, 原因: {e}")

if __name__ == "__main__":

    # 配置你的網站信息
    load_dotenv()
    # URL STUFF
    BASE_URL = os.getenv("BASE_URL")
    NEXT_URL = os.getenv("NEXT_URL")
    LOGIN_URL = os.getenv("LOGIN_URL")
    # LOGIN STUFF
    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")
    # HEADERS STUFF
    HEADERS = {"User-Agent": os.getenv("USER_AGENT"),
               "referer": os.getenv("REFERER")
               }

    # parse保存所有url的json檔
    file_name = "urls.json"
    all_urls = read_json(file_name)
    all_urls_len = len(all_urls)

    # 創建爬蟲實例，並且進入登入狀態
    crawler = WebCrawlerForImg(base_url=BASE_URL, headers=HEADERS, login_url=LOGIN_URL, username=USERNAME, password=PASSWORD)
    #crawler.crawl(url_generator(all_urls), all_urls_len)

