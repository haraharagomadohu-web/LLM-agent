import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("NOTION_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

print("--- Notion 接続確認中 ---")
response = requests.post(
    "https://api.notion.com/v1/search",
    headers=headers,
    json={"filter": {"property": "object", "value": "database"}}
)

if response.status_code == 200:
    results = response.json().get("results", [])
    if not results:
        print("❌ データベースが見つかりません。")
        print("考えられる原因:")
        print("1. Notionのデータベース画面右上の '...' -> 'コネクトの追加' でインテグレーションをまだ招待していない。")
        print("2. トークンが間違っている。")
    else:
        print(f"✅ {len(results)}個のデータベースが見つかりました：\n")
        for db in results:
            title = db['title'][0]['plain_text'] if db['title'] else "タイトルなし"
            print(f"名前: {title}")
            print(f"ID  : {db['id']}")
            print("-" * 30)
else:
    print(f"❌ エラーが発生しました (Status: {response.status_code})")
    print(response.json())
