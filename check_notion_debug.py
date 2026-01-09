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

print("--- Notion Search ---")
response = requests.post(
    "https://api.notion.com/v1/search",
    headers=headers,
    json={"filter": {"property": "object", "value": "database"}}
)

if response.status_code == 200:
    results = response.json().get("results", [])
    for db in results:
        raw_id = db['id']
        clean_id = raw_id.replace('-', '')
        print(f"Name: {db['title'][0]['plain_text'] if db['title'] else 'Untitled'}")
        print(f"Raw ID: {raw_id}")
        print(f"Clean ID: {clean_id}")
        print(f"Length: {len(clean_id)}")
else:
    print(response.json())
