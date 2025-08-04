from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL1 = "https://www.chemotherapy.or.jp/modules/newslist/index.php?content_id=3"
BASE_URL2 = "https://www.chemotherapy.or.jp/modules/newslist/index.php?content_id=4"
GAKKAI = "日本化学療法学会"

def generate_rss(items, output_path):
    fg = FeedGenerator()
    fg.title(f"{GAKKAI}トピックス")
    fg.link(href=BASE_URL1)
    fg.description(f"{GAKKAI}の最新トピック情報")
    fg.language("ja")
    fg.generator("python-feedgen")
    fg.docs("http://www.rssboard.org/rss-specification")
    fg.lastBuildDate(datetime.now(timezone.utc))

    for item in items:
        entry = fg.add_entry()
        entry.title(item['title'])
        entry.link(href=item['link'])
        entry.description(item['description'])
        entry.guid(item['link'], permalink=True)
        entry.pubDate(item['pub_date'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fg.rss_file(output_path)
    print(f"\n✅ RSSフィード生成完了！📄 保存先: {output_path}")


def extract_items1(page):
    
    selector = "div.box_topics div.title_news"
    
    page.wait_for_selector(selector, timeout=10000) 
    
    blocks = page.locator(selector)
    count = blocks.count()
    print(f"📦 発見した記事数: {count}")
    items1 = []

    max_items = 10
    for i in range(min(count, max_items)):
        try:
            block = blocks.nth(i)

            # 🕒 日付を現在時刻に固定
            pub_date = datetime.now(timezone.utc)

            title = block.locator("a").first.inner_text().strip()
                
            try:
                href = block.locator("a").first.get_attribute("href")
                full_link = urljoin(BASE_URL1, href)
            except:
                href = ""
                full_link = BASE_URL1

            if not title or not href:
                print(f"⚠ 必須フィールドが欠落したためスキップ（{i+1}行目）: title='{title}', href='{href}'")
                continue
            
            items1.append({
                "title": title,
                "link": full_link,
                "description": title,
                "pub_date": pub_date
            })

        except Exception as e:
            print(f"⚠ 行{i+1}の解析に失敗: {e}")
            continue
            
    return items1

def extract_items2(page):
    
    selector = "div.box_topics div.news_title"
    
    page.wait_for_selector(selector, timeout=10000) 
    
    blocks = page.locator(selector)
    count = blocks.count()
    print(f"📦 発見した記事数: {count}")
    items2 = []

    max_items = 10
    for i in range(min(count, max_items)):
        try:
            block = blocks.nth(i)

            # 🕒 日付を現在時刻に固定
            pub_date = datetime.now(timezone.utc)

            title = block.locator("a").first.inner_text().strip()
                
            try:
                href = block.locator("a").first.get_attribute("href")
                full_link = urljoin(BASE_URL2, href)
            except:
                href = ""
                full_link = BASE_URL2

            if not title or not href:
                print(f"⚠ 必須フィールドが欠落したためスキップ（{i+1}行目）: title='{title}', href='{href}'")
                continue
            
            items2.append({
                "title": title,
                "link": full_link,
                "description": title,
                "pub_date": pub_date
            })

        except Exception as e:
            print(f"⚠ 行{i+1}の解析に失敗: {e}")
            continue
            
    return items2

# ===== 実行ブロック =====
with sync_playwright() as p:
    print("▶ ブラウザを起動中...")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        print("▶ ページにアクセス中...")
        page.goto(BASE_URL1, timeout=30000)
        page.wait_for_load_state("load", timeout=30000)
    except PlaywrightTimeoutError:
        print("⚠ ページの読み込みに失敗しました。")
        browser.close()
        exit()

    print("▶ 記事を抽出しています...")
    items1 = extract_items1(page)

    if not items1:
        print("⚠ 抽出できた記事がありません。HTML構造が変わっている可能性があります。")
    
    try:
        print("▶ ページにアクセス中...")
        page.goto(BASE_URL2, timeout=30000)
        page.wait_for_load_state("load", timeout=30000)
    except PlaywrightTimeoutError:
        print("⚠ ページの読み込みに失敗しました。")
        browser.close()
        exit()

    print("▶ 記事を抽出しています...")
    items2 = extract_items2(page)
    
    if not items2:
        print("⚠ 抽出できた記事がありません。HTML構造が変わっている可能性があります。")

    items = items1 + items2
    
    rss_path = "rss_output/Feed4.xml"
    generate_rss(items, rss_path)
    browser.close()
