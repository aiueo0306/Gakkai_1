from glob import glob
import feedparser
from feedgen.feed import FeedGenerator

fg = FeedGenerator()
fg.title('学会RSS統合')
fg.link(href='https://example.com/rss_output/combined3.xml', rel='self')
fg.description('複数フィードを統合したマスターRSS')
fg.language('ja')

for xml_file in glob('rss_output/*.xml'):
    if 'combined.xml' in xml_file:
        continue  # 自分自身はスキップ

    d = feedparser.parse(xml_file)

    # 例：「日本緩和医療薬学会トピックス」→「日本緩和医療薬学会」
    feed_title = d.feed.get("title", "")
    if feed_title.endswith("トピックス"):
        source = feed_title.replace("トピックス", "").strip()
    else:
        source = feed_title.strip() or "出典不明"

    for entry in d.entries:
        fe = fg.add_entry()
        # タイトルの前に【学会名】を付ける（あなたの要望に基づく）
        fe.title(f"【{source}】{entry.title}")
        fe.link(href=entry.link)
        fe.description(entry.get("summary", ""))
        fe.pubDate(entry.get("published", ""))
        fe.guid(entry.link + "#" + entry.get("published", "2025"))
        
fg.rss_file('rss_output/combined.xml')
