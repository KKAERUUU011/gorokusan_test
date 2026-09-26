"""
563A の株価を みんかぶ(minkabu.jp) のページから取得できるかを確認するテストスクリプト(v3)。
GitHub Actions 上で手動実行して、単純な HTTP GET + パースで価格が取れるかどうかを確認する。
本番アプリ(gorokusan-tracker)には一切触れない、完全に独立した検証用コード。

v1: Yahoo!ファイナンス + __NEXT_DATA__ → 見つからず
v2: Yahoo!ファイナンス + 広めのキーワード検索 → 価格情報自体がHTMLになく断念
v3: みんかぶ(minkabu.jp) → 静的HTMLに価格が乗っていそうなので試す
"""
import re
import sys

import requests

URL = "https://minkabu.jp/stock/563A"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def find_keyword_context(html, keyword, radius=200, max_hits=5):
    hits = []
    start = 0
    while True:
        idx = html.find(keyword, start)
        if idx == -1:
            break
        s = max(0, idx - radius)
        e = min(len(html), idx + len(keyword) + radius)
        hits.append(html[s:e])
        start = idx + len(keyword)
        if len(hits) >= max_hits:
            break
    return hits


def try_price_regex(html):
    # 「取引価格」や「株価」の近くにある数値(カンマ・小数点を含む)を拾う
    patterns = [
        r"取引価格[^0-9]{0,30}([0-9,]+\.?[0-9]*)",
        r"現在値[^0-9]{0,30}([0-9,]+\.?[0-9]*)",
        r'"price"\s*:\s*"?([0-9,.]+)"?',
    ]
    results = []
    for p in patterns:
        m = re.search(p, html)
        if m:
            results.append((p, m.group(1)))
    return results


def main():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    html = resp.text
    print(f"HTTPステータス: {resp.status_code}")
    print(f"取得バイト数: {len(html)}")

    if resp.status_code != 200:
        print("NG: ページ取得自体に失敗しました。")
        print("冒頭500文字:")
        print(html[:500])
        sys.exit(1)

    regex_hits = try_price_regex(html)
    if regex_hits:
        print("\n=== 正規表現で見つかった価格らしき値 ===")
        for pattern, val in regex_hits:
            print(f"  pattern={pattern!r} -> {val}")
    else:
        print("\n正規表現では見つかりませんでした。")

    for kw in ["取引価格", "現在値", "563A"]:
        hits = find_keyword_context(html, kw, radius=150, max_hits=3)
        if hits:
            print(f"\n=== キーワード「{kw}」の周辺 ===")
            for h in hits:
                print(h)

    if not regex_hits:
        print("\nNG: 価格が見つかりませんでした。")
        sys.exit(1)

    print("\n上のヒット内容に実際の株価の数値が含まれているか、目視で確認してください。")


if __name__ == "__main__":
    main()
