from WebCrawlerSelenium import WebCrawlerSelenium
from util import read_json, get_batch, url_generator, time_stoper
import os
from dotenv import load_dotenv

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

    # 59份，分成3批16份，餘11，總共分4批進行
    day = 4
    batch_len, batch_start_idx, batch_urls = get_batch(all_urls, batch_number=day)

    # 創建爬蟲實例
    crawler = WebCrawlerSelenium(base_url=BASE_URL, login_url=LOGIN_URL, username=EMAIL, password=PASSWORD)
    crawler.login()
    crawler.crawl(url_provider=url_generator(batch_urls), loop_times=batch_len, start_idx=batch_start_idx)

    print("執行結束，按 Ctrl+C 關閉程序或手動關閉瀏覽器。")
    try:
        while True:
            time_stoper(1)
    except KeyboardInterrupt:
        print("程序結束，關閉瀏覽器。")
        crawler.close_browser()