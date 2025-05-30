from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ========= 基本設定 =========
BASE_URL = "https://www.secretariat.ne.jp/jsmd/"  # またはそのトップページURL
DEFAULT_LINK1 = "https://www.secretariat.ne.jp/jsmd/info/info-shintyaku-index.html"
DEFAULT_LINK2 = "https://www.secretariat.ne.jp/jsmd/info/info-index.html"
ORG_NAME = "日本うつ病学会"

# ========= RSS生成関数 =========
def generate_rss(items, output_path):
    fg = FeedGenerator()
    fg.title(f"{ORG_NAME}トピックス")
    fg.link(href=BASE_URL)
    fg.description(f"{ORG_NAME}の最新トピック情報")
    fg.language("ja")
    fg.generator("python-feedgen")
    fg.docs("http://www.rssboard.org/rss-specification")
    fg.lastBuildDate(datetime.now(timezone.utc))

    for item in items:
        entry = fg.add_entry()
        entry.title(item['title'])
        entry.link(href=item['link'])
        entry.description(item['description'])
        guid_value = f"{item['link']}#{item['pub_date'].strftime('%Y%m%d')}"
        entry.guid(guid_value, permalink=False)
        entry.pubDate(item['pub_date'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fg.rss_file(output_path)
    print(f"\n✅ RSSフィード生成完了！📄 保存先: {output_path}")

# ========= 抽出関数①（新着情報） =========
def extract_items1(page):
    rows = page.locator("tr:has(th time):has(td a.external)")
    count = rows.count()
    print(f"📦 発見した記事数: {count}")
    items = []

    for i in range(count):
        try:
            row = rows.nth(i)

            # 📅 <time> タグの datetime 属性を ISO 形式で取得
            time_tag = row.locator("th time")
            iso_date = time_tag.get_attribute("datetime")  # e.g. '2020-05-22'
            pub_date = datetime.fromisoformat(iso_date).replace(tzinfo=timezone.utc)

            # 🔗 <td> 内の <a class="external">
            a_tag = row.locator("td a.external").first
            title = a_tag.inner_text().strip()
            href = a_tag.get_attribute("href")
            full_link = urljoin(BASE_URL, href)

            # 📝 <td> 全体のテキストを説明文に
            description = row.locator("td").inner_text().strip()

            items.append({
                "title": title,
                "link": full_link,
                "description": description,
                "pub_date": pub_date
            })

        except Exception as e:
            print(f"⚠ 行{i+1}の解析に失敗: {e}")
            continue

    return items

# ========= 抽出関数②（お知らせ一覧） =========
def extract_items2(page):
    rows = page.locator("tr:has(th time):has(td a)")
    count = rows.count()
    print(f"📦 発見した記事数: {count}")
    items = []

    for i in range(count):
        try:
            row = rows.nth(i)

            # 📅 日付：<time datetime="YYYY-MM-DD"> → ISO形式で取得
            time_tag = row.locator("th time")
            iso_date = time_tag.get_attribute("datetime")
            pub_date = datetime.fromisoformat(iso_date).replace(tzinfo=timezone.utc)

            # 🔗 タイトルとリンク
            a_tag = row.locator("td a").first
            title = a_tag.inner_text().strip()
            href = a_tag.get_attribute("href")
            full_link = urljoin(BASE_URL, href)

            # 📝 説明文：<td> の中身すべて
            description = row.locator("td").inner_text().strip()

            items.append({
                "title": title,
                "link": full_link,
                "description": description,
                "pub_date": pub_date
            })

        except Exception as e:
            print(f"⚠ 行{i+1}の解析に失敗: {e}")
            continue

    return items


# ========= 実行ブロック =========
with sync_playwright() as p:
    print("▶ ブラウザを起動中...")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()

    # --- ページ1 ---
    page1 = context.new_page()
    try:
        print("▶ [1ページ目] アクセス中...")
        page1.goto(DEFAULT_LINK1, timeout=30000)
        page1.wait_for_load_state("load", timeout=30000)
        items1 = extract_items1(page1)
        if not items1:
            print("⚠ [1ページ目] 抽出できた記事がありません。")
    except PlaywrightTimeoutError:
        print("⚠ [1ページ目] 読み込み失敗")
        items1 = []

    # --- ページ2 ---
    page2 = context.new_page()
    try:
        print("▶ [2ページ目] アクセス中...")
        page2.goto(DEFAULT_LINK2, timeout=30000)
        page2.wait_for_load_state("load", timeout=30000)
        items2 = extract_items2(page2)
        if not items2:
            print("⚠ [2ページ目] 抽出できた記事がありません。")
    except PlaywrightTimeoutError:
        print("⚠ [2ページ目] 読み込み失敗")
        items2 = []

    # --- 統合 + 並べ替え ---
    items = items1 + items2
    items.sort(key=lambda x: x["pub_date"], reverse=True)

    # --- RSS生成 ---
    rss_path = "rss_output/Feed20.xml"
    generate_rss(items, rss_path)

    browser.close()
