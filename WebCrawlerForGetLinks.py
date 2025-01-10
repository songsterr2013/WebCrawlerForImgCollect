import time
import random
import os
from dotenv import load_dotenv
from util import to_json
import cloudscraper
from bs4 import BeautifulSoup

class WebCrawlerForGetLinks:
    def __init__(self, base_url, next_url, headers):
        self.all_links = []
        self.base_url = base_url
        self.next_url = next_url
        self.headers = headers
        self.session = cloudscraper.create_scraper()

    def get_all_target_links(self, delay=2):

        # 第一次先進首頁
        response = self.session.get(self.base_url)
        print('進入首頁中...', response.status_code)

        # 停一下
        time.sleep(delay + random.uniform(0, 1))

        # 然後再進指定想爬的主頁面(已知最大頁數為4)
        page = 1
        middle_url = '?page='
        while page != 5:
            link_w_page = self.next_url+middle_url+str(page)

            print(f'進入到主爬蟲頁面第{page}頁中...')
            soup = self.fetch_page(link_w_page)

            links = soup.find_all("a", {"class": "media-cover"})
            for link in links:
                href = link.get("href")
                if href:
                    # 拼接完整網址（如果需要）
                    full_url = f"{self.base_url}{href}"
                    self.all_links.append(full_url)
                    print(full_url)

            page += 1

        return self.all_links

    def fetch_page(self, url, max_retries=5, delay=2):
        retries = 0
        while retries < max_retries:
            try:
                print(f"=正在嘗試爬取: {url} (第 {retries + 1} 次)")
                response = self.session.get(url, headers=self.headers)

                # 檢查狀態碼
                if response.status_code == 200:
                    print(f"==成功爬取: {url}")
                    return BeautifulSoup(response.text, 'html.parser')
                else:
                    print(f"==錯誤狀態碼: {response.status_code}")

            except Exception as e:
                print(f"==錯誤: {e}")

            # 增加重試次數
            retries += 1
            print(f"==重試中... ({retries}/{max_retries})")
            time.sleep(delay + random.uniform(0, 1))

        print(f"==爬取失敗: {url}")
        return None

if __name__ == "__main__":

    # 配置網站信息
    load_dotenv()  # load config from .env
    BASE_URL = os.getenv("BASE_URL")
    NEXT_URL = os.getenv("NEXT_URL")
    HEADERS = {"User-Agent": os.getenv("USER_AGENT"),
               "referer": os.getenv("REFERER")
               }

    # 創建爬蟲實例並取得所有主要URL
    crawler = WebCrawlerForGetLinks(base_url=BASE_URL, next_url=NEXT_URL, headers=HEADERS)
    all_links = crawler.get_all_target_links()
    to_json(all_links)