from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from urllib.parse import quote
from bs4 import BeautifulSoup
import time

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask

import json

def get_twitter_links_with_login(tag, ipass_txt):
    # ログイン情報を読み込む
    ######ipass.txtの中身########
    #{
        #"username":"@hoge",
        #"password":"h0g3"
    #}

    with open(ipass_txt, 'r') as f:
        ipass = json.load(f)
    username=ipass["username"]
    password=ipass["password"]

    # WebDriverのパスを指定
    driver = webdriver.Edge()

    # Twitterにアクセスする
    driver.get('https://twitter.com/login')
    time.sleep(2)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'input')))
    # ユーザー名とパスワードを入力する
    # うまくいかない場合、ブラウザ標準の解析ツールからinputのxpathを取得して()内を書き換える
    input_username = driver.find_element_by_xpath('//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[5]/label/div/div[2]/div/input')
    time.sleep(1)
    input_username.send_keys(username)
    input_username.send_keys(Keys.RETURN)
    time.sleep(1)
    # うまくいかない場合、ブラウザ標準の解析ツールからinputのxpathを取得して()内を書き換える
    input_password = driver.find_element_by_xpath('//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[3]/div/label/div/div[2]/div[1]/input')
    input_password.send_keys(password)
    time.sleep(1)
    input_password.send_keys(Keys.RETURN)

    # ログイン成功後に検索結果ページを取得
    # タグをURLエンコード
    search_query = quote(tag)
    time.sleep(1)#これがないとbot判定ではじかれる
    search_url = f'https://twitter.com/hashtag/{search_query}?src=hashtag_click&f=live'
    driver.get(search_url)
    time.sleep(2)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'article')))
    html = driver.page_source

    #lazy loadされてる部分を読み込むために、スクロールダウンしていく
    lastHeight = driver.execute_script("return document.body.scrollHeight")  # スクロールされてるか判断する部分
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # スクロールダウン
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'article')))
        html += driver.page_source
        # スクロールされてるか判断する部分
        newHeight = driver.execute_script("return document.body.scrollHeight")
        if newHeight == lastHeight:
            break
        lastHeight = newHeight
    
    soup = BeautifulSoup(html, 'html.parser')

    tweet_links = []
    for a in soup.find_all('a', {'role': 'link'}):
        #この辺は細かいUIによって調整が必要になるかも。
        if '/status/' in a['href'] and not 'photo' in a['href'] and not 'analytics' in a['href']:
            tweet_links.append(f'https://twitter.com{a["href"]}')
    driver.close()
    driver.quit()
    return list(set(tweet_links))


def get_tweet_ss(url, fname):
    driver = webdriver.Edge()

    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'article')))
    w = driver.execute_script('return document.body.scrollWidth')
    h = driver.execute_script('return document.body.scrollHeight')
    driver.set_window_size(w, h)
    # スクリーンショットの保存
    png = driver.find_element_by_tag_name('article').screenshot_as_png
    # ファイルに保存
    with open(f'./{fname}.png', 'wb') as f:
        f.write(png)
    driver.close()
    driver.quit()

def gen_qr(url, fname):
    qr = qrcode.make(url)
    qr.save(f'./{fname}.png', image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer(), color_mask=RadialGradiantColorMask())

if __name__=="__main__":
    # タグとログイン情報を指定してツイートのリンクを取得
    tweetLinks=get_twitter_links_with_login('なんらかのタグ', "ipass.txt")

    # ツイートのリンクからツイート部分のスクリーンショットとQRコードを生成
    for i, url in enumerate(tweetLinks):
        get_tweet_ss(url, "img/ss"+str(i))
        gen_qr(url, "img/qr"+str(i))
