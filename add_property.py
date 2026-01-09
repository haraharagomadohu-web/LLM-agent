import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID").replace("-", "")

def add_no_property():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    payload = {
        "properties": {
            "No.": {
                "rich_text": {}
            }
        }
    }
    
    print(f"Adding 'No.' property to database: {NOTION_DATABASE_ID}...")
    res = requests.patch(url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("✅ プロパティ 'No.' を正常に追加しました！")
    else:
        print(f"❌ エラーが発生しました (Status: {res.status_code})")
        print(res.json())

if __name__ == "__main__":
    add_no_property()
