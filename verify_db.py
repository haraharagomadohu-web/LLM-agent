import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("NOTION_TOKEN")
db_id = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

print(f"Checking DB: {db_id}")
response = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers)

if response.status_code == 200:
    results = response.json().get("results", [])
    print(f"Found {len(results)} pages in DB.")
    for page in results:
        try:
            name = page['properties']['Name']['title'][0]['text']['content']
            date = page['properties']['Date']['date']['start']
            print(f"- {name} ({date})")
        except:
            print("- (Untitled or missing properties)")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
