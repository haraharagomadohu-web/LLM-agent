import requests
import json

NOTION_TOKEN = "ntn_Y12448129326WznXa8qQcfXv7sEeefdxSMkOlAuAONn4xd"

def find_page():
    """連携されているページを探す"""
    url = "https://api.notion.com/v1/search"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {
        "filter": {"property": "object", "value": "page"}
    }
    response = requests.post(url, json=payload, headers=headers)
    pages = response.json().get("results", [])
    return pages[0] if pages else None

def create_database(parent_page_id):
    """指定したページの下にデータベースを作成する"""
    url = "https://api.notion.com/v1/databases"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "AIエージェント開発ログ (世界地図)"}}],
        "properties": {
            "Name": {"title": {}},
            "Date": {"date": {}},
            "Tools": {"rich_text": {}},
            "GitHub": {"url": {}}
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

if __name__ == "__main__":
    print("Notionの親ページを検索中...")
    page = find_page()
    if page:
        print(f"親ページが見つかりました: {page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')}")
        print("データベースを作成中...")
        db = create_database(page['id'])
        if 'id' in db:
            print(f"成功! データベースID: {db['id']}")
            print(f"URL: {db.get('url')}")
        else:
            print("データベース作成に失敗しました。")
            print(json.dumps(db, indent=2))
    else:
        print("連携されたページが見つかりません。")
        print("あらかじめNotionで適当なページ（または親となるページ）を作成し、")
        print("右上の '...' -> 'Add connections' から作成したインテグレーションを招待してください。")
