import os
import pickle
from dotenv import load_dotenv
from util import read_json, url_generator, time_stoper, make_folder
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import cloudscraper

class WebCrawlerForImg:
    def __init__(self, base_url, headers=None, login_url=None, username=None, password=None, cookies_file="cookies.pkl"):
        self.base_url = base_url
        self.headers = headers
        self.login_url = login_url
        self.username = username
        self.password = password
        self.cookies_file = cookies_file

        self.main_dir_name = "Downloaded_images"
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',
                'platform': 'windows',
                'mobile': False
            },
            delay=10
        )

    def login(self):
        """
        模擬登入網站
        """
        print("==========Logging in...==========")

        payload = {
            "username": f"{self.username}",
            "password": f"{self.password}"
        }

        # 第一次先進首頁，目前觀察出現403的情況頗高，但一旦只要出現200，往後爬蟲一路暢通無阻
        response = self.session.get(self.base_url)
        print(f'進入首頁中...請求狀態:{response.status_code}')
        time_stoper(2)

        # 進入登入頁面，而不是直接POST，模擬真實使用者的動者
        response = self.session.get(self.login_url)#, headers=self.headers)
        print(f'進入登入頁面中...請求狀態:{response.status_code}')
        time_stoper(2)

        # 執行登入動作並獲取cookies
        post_response = self.session.post(self.login_url, data=payload)#, headers=self.headers)
        if post_response.status_code == 200:
            soup = BeautifulSoup(post_response.text, 'html.parser')
            print(soup)
            # 查找是否包含 "user" 字眼，來判斷是否成功登入
            if "user" in soup.text:
                print("登入成功!")
                self.save_cookies()
            else:
                print("依然無法登入，程式將直接關閉")
                exit()
        else:
            raise Exception(f"登入失敗，請求狀態：{post_response.status_code}")
        time_stoper(2)

    def crawl(self, url_provider:list, loop_times:int):
        """
        主要爬取的動作都寫在這邊
        基於util中的url_generator生成器，對json進行parse後所取得的url，然後進行爬蟲
        """
        # 先進首頁，目前觀察出現403的情況頗高，但一旦只要出現200，往後爬蟲一路暢通無阻
        response = self.session.get(self.base_url)
        print(f'進入首頁中...請求狀態:{response.status_code}')

        for count, url in enumerate(url_provider):
            time_stoper(1) # 隨機暫停器
            loop = count + 1
            folder_name = f"{loop}_{url.rsplit('/', 1)[-1]}"
            print(f"==========({loop} / {loop_times}) 爬取: {url}", '==========')

            # 1.基於list中的url進入指定的網址並取得所有圖片的url
            to_download = self.get_all_images(url)

            # 2.建立最外圍folder
            make_folder(self.main_dir_name)

            # 3.基於第1步所取得的所有url進行下載
            self.download_images(img_urls=url_generator(to_download), dir_name=folder_name)

    def get_all_images(self, url:str):
        """
        獲取所有目標img的url，且執行recur動作前往下一頁
        """
        print("==========正在獲取目標底下的所有子url...==========")
        img_urls = []
        self.crawl_img(url, img_urls)
        print(img_urls)
        return img_urls

    def crawl_img(self, url:str, img_urls:list, count=-1):
        """
        基於對html的parse，提取所有目標img的url，最後return出一個list
        """
        response = self.session.get(url)#, headers=self.headers)
        print(f'進入目標頁面{url}中...請求狀態:{response.status_code}, 遞迴次數: {count + 1}' )

        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup)
        div_blocks = soup.find_all("div", class_="album-photo my-2")

        for div in div_blocks:
            img_tag = div.find("img", {"data-src": True})
            if img_tag:
                img_urls.append(img_tag["data-src"])

        # 檢查是否有下一頁
        main_wrap = soup.find('div', class_='container main-wrap')
        if main_wrap:
            next_page_link = main_wrap.find('nav', class_='py-2', attrs={'aria-label': 'Page navigation'})
            next_page = next_page_link.find('a', string='Next')
            if next_page and next_page.get('href'):
                next_page_url = urljoin(self.base_url, next_page['href'])
                # 遞迴進入下一頁
                print(f"已取得下一頁的URL:{next_page_url}")
                self.crawl_img(next_page_url, img_urls, count + 1)


    def download_images(self, img_urls:list, dir_name):
        """
        對img_urls中的url一個一個access並下載保存到本地
        """
        img_urls_len = len(img_urls)

        # 在主folder中建立子folder
        batch_folder_path = os.path.join(self.main_dir_name, dir_name)
        make_folder(batch_folder_path)

        for count, img_url in enumerate(img_urls):
            time_stoper(2)
            new_count = count+1

            print(f'正在處理當前頁面的第 {new_count} / {img_urls_len} 張圖片')

            try:
                # 獲取圖片內容
                print(f"正在下載圖片: {img_url}")
                response = self.session.get(img_url, stream=True)#, headers=self.headers)  # 使用 stream 提升大文件處理效率
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

    def save_cookies(self):
        """Save Cookie into file"""
        with open(self.cookies_file, "wb") as f:
            pickle.dump(self.session.cookies, f)
        print("Cookie 已保存到文件。")

    def load_cookies(self):
        """Load and update Cookie """
        try:
            with open(self.cookies_file, "rb") as f:
                self.session.cookies.update(pickle.load(f))
            print("Cookie 已成功加載。")
        except FileNotFoundError:
            print("Cookie 文件不存在。")

    def is_cookies_valid(self):
        """檢查當前的 cookies 是否有效，通過發送請求來判斷"""
        print("==========檢查cookies是否有效中...==========")
        try:
            # 第一次先進首頁，目前觀察出現403的情況頗高，但一旦只要出現200，往後爬蟲一路暢通無阻
            response = self.session.get(self.base_url)
            print(f'進入首頁中...請求狀態:{response.status_code}')
            time_stoper(2)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 查找是否包含 "Login" 的字眼，來判斷是否已登入
                if "Login" in soup.text:
                    print("尚未登入。")
                    return False
                else:
                    print("Cookies 有效，處於登入狀態。")
                    return True
            else:
                print(f"無法訪問會員設定頁面，HTTP狀態碼: {response.status_code}")
                return False

        except Exception as e:
            print(f"檢查 cookies 時出錯: {e}")
            return False

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
    crawler.load_cookies()

    # 檢查 cookies 是否有效，如果無效則執行登入
    if not crawler.is_cookies_valid():
        crawler.login()
    else:
        print("繼續使用已加載的 cookies 進行操作。")

    crawler.crawl(url_provider=url_generator(all_urls), loop_times=all_urls_len)

