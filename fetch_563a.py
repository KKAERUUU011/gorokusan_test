"""
563A の株価を Yahoo!ファイナンスのページから取得できるかを確認するためのテストスクリプト(v2)。
GitHub Actions 上で手動実行して、単純な HTTP GET + パースで価格が取れるかどうかを確認する。
本番アプリ(gorokusan-tracker)には一切触れない、完全に独立した検証用コード。

v1では __NEXT_DATA__ / 単純な正規表現で見つからなかったため、
Next.js の RSC ストリーミング(self.__next_f.push(...))も含めて広く探すように変更。
"""
import re
import sys

import requests

URL = "https://finance.yahoo.co.jp/quote/563A.T"
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


def main():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    html = resp.text
    print(f"HTTPステータス: {resp.status_code}")
    print(f"取得バイト数: {len(html)}")

    if resp.status_code != 200:
        print("NG: ページ取得自体に失敗しました。")
        sys.exit(1)

    # 通常の「現在値」表記
    found_any = False
    for kw in ["現在値", "regularMarketPrice", "\\u73fe\\u5728\\u5024"]:
        hits = find_keyword_context(html, kw)
        if hits:
            found_any = True
            print(f"\n=== キーワード「{kw}」がヒット({len(hits)}件、うち最大5件表示) ===")
            for i, h in enumerate(hits):
                print(f"--- hit {i+1} ---")
                print(h)

    # 563A自体の名称やティッカーの近く数百文字も見ておく(構造把握用)
    for kw in ["563A", "GX ＮＡＳＤＡＱ", "カバード・コール"]:
        hits = find_keyword_context(html, kw, radius=150, max_hits=2)
        if hits:
            print(f"\n=== キーワード「{kw}」の周辺 ===")
            for h in hits:
                print(h)

    if not found_any:
        print("\nNG: 価格らしきキーワードが見つかりませんでした。")
        print("ページの主要部分がクライアント側JS実行後にしか現れない可能性があります。")
        sys.exit(1)

    print("\n上のヒット内容に実際の株価の数値が含まれているか、目視で確認してください。")


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
