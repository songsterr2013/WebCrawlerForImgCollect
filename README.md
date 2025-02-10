# 漫畫網站實現自動化爬蟲
## 動機:
#### 本練習基於個人興趣，嘗試從漫畫網站中爬取指定的漫畫，練習過程中有以下收獲:
* 使用在Selenium基礎上更進階的Seleniumbase
* 了解到Cloudscraper的人類驗證基本運作原則，在登入過程中受到Cloudflare的各種阻撓
* 加入各種模擬手段，貼近真實使用者的操作，如時間暫停、滑鼠移動、基於referer跳轉等
* 最終發現最佳解是在一切自動化前的登入環節中設置15秒的空檔，進行手動點撃認證和手動輸入帳號密碼
* 一旦突破登入環節，往後的自動化爬取過程中將暢通無阻

## 各檔案的基本說明:
#### 使用Cloudscraper + Seleniumbase攻克Cloudflare，實現自動化爬蟲
* WebCrawlerForGetLinks.py -> 使用cloudscraper爬取一般網頁，內部邏輯和HTML PARSE結構目前屬於爬取圖片URL專用。
* WebCrawlerForImg.py -> 可解決一般無需人類驗證的登入，在保持登入狀態下，基於提供的URL進行下載
* WebCrawlerSelenium + selenium_main -> 能繞過Cloudflare的點撃認證，在保持登入狀態下，基於提供的URL進行圖片下載。  

## 圖片下載方法:
####  實現圖片下載的方法依賴seleniumbase中的execute_script
* 由於一般的做法是獲取url後透過requests下載，但會導致脫離登入狀態，處理起來較麻煩，尤其在Cloudflare驗證之下
* 因此利用JavaScript中的canvas來繪製圖像
* 但前題是，圖片未設置CORS安全策略，如有，照片tainted將無法繪製
