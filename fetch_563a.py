"""
563A の株価を Yahoo!ファイナンスのページから取得できるかを確認するためのテストスクリプト。
GitHub Actions 上で手動実行して、単純な HTTP GET + パースで価格が取れるかどうかを確認する。
本番アプリ(gorokusan-tracker)には一切触れない、完全に独立した検証用コード。
"""
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

URL = "https://finance.yahoo.co.jp/quote/563A.T"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def try_next_data(soup):
    """Next.js の __NEXT_DATA__ script タグから価格らしき数値を探す。"""
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        return None
    try:
        data = json.loads(tag.string)
    except json.JSONDecodeError:
        return None

    # price / regularMarketPrice っぽいキーを再帰的に探す
    candidates = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, (int, float)) and re.search(
                    r"price|Price", k
                ):
                    candidates.append((k, v))
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return candidates or None


def try_regex_fallback(html):
    """HTML 全文から「現在値」付近の数値を正規表現で拾う簡易フォールバック。"""
    m = re.search(r"現在値[^0-9]{0,20}([0-9,]+\.?[0-9]*)", html)
    if m:
        return m.group(1)
    # メタタグ等に埋め込まれているケース
    m = re.search(r'"regularMarketPrice"\s*:\s*"?([0-9,.]+)"?', html)
    if m:
        return m.group(1)
    return None


def main():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    print(f"HTTPステータス: {resp.status_code}")
    print(f"取得バイト数: {len(resp.text)}")

    if resp.status_code != 200:
        print("NG: ページ取得自体に失敗しました。")
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")

    result = try_next_data(soup)
    if result:
        print("=== __NEXT_DATA__ から見つかった price 系フィールド ===")
        for k, v in result[:20]:
            print(f"  {k}: {v}")
    else:
        print("__NEXT_DATA__ からは見つかりませんでした。")

    fallback = try_regex_fallback(resp.text)
    if fallback:
        print(f"=== 正規表現フォールバックで見つかった値: {fallback} ===")
    else:
        print("正規表現フォールバックでも見つかりませんでした。")

    if not result and not fallback:
        print("\nNG: どちらの方法でも価格が見つかりませんでした。")
        print("ページ冒頭2000文字を出力します(構造確認用):\n")
        print(resp.text[:2000])
        sys.exit(1)

    print("\n判定: 少なくとも一部の方法で価格らしき値が取得できました。")
    print("上のログの数値が実際の563Aの株価と一致するか、目視で確認してください。")


if __name__ == "__main__":
    main()
