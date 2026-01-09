import os
import json
import shutil
import datetime
from pathlib import Path
from dotenv import load_dotenv
import openai
import requests
from git import Repo
import tweepy

# .envの読み込み
load_dotenv()

def get_env_safe(key):
    val = os.getenv(key)
    if val: return val.strip().strip("'").strip('"')
    return None

# 各種設定
OPENAI_API_KEY = get_env_safe("OPENAI_API_KEY")
GEMINI_API_KEY = get_env_safe("GEMINI_API_KEY")
NOTION_TOKEN = get_env_safe("NOTION_TOKEN")
NOTION_DATABASE_ID = get_env_safe("NOTION_DATABASE_ID")
GITHUB_REPO_PATH = get_env_safe("GITHUB_REPO_PATH")
GITHUB_USER_NAME = get_env_safe("GITHUB_USER_NAME")
GITHUB_TOKEN = get_env_safe("GITHUB_TOKEN")
TWITTER_API_KEY = get_env_safe("TWITTER_API_KEY")
TWITTER_API_SECRET = get_env_safe("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = get_env_safe("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = get_env_safe("TWITTER_ACCESS_SECRET")

# 一意のプロジェクトIDとして現在のフォルダ名を使用
PROJECT_ID = os.path.basename(os.getcwd())

INPUT_DIR = Path("inputs")
ARCHIVE_DIR = INPUT_DIR / "archived"

def analyze_markdown(content):
    """LLMを使用してプロジェクト情報を抽出する"""
    clipped_content = content[-15000:] if len(content) > 15000 else content
    prompt = f"""
    以下のチャット履歴からプログラミングプロジェクトの要約を生成してください。
    【出力形式】必ず以下のキーを持つJSON
    - title: プロジェクトの表示名 (15文字以内)
    - tools: 言語/ツール (カンマ区切り)
    - insights: 今回の「更新内容（何を追加・修正したか）」の短い要約
    - x_summary: X用紹介文 (80文字程度)
    
    【チャット履歴】
    {clipped_content}
    """
    
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
        res = client.models.generate_content(
            model='gemini-2.0-flash', contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        data = json.loads(res.text)
        return data[0] if isinstance(data, list) else data
    except Exception as e:
        print(f"Gemini解析エラー: {e}")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)

def find_notion_page_by_id(project_id):
    """ProjectIDプロパティを使ってNotionの既存ページを探す"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID.replace('-', '')}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {"filter": {"property": "ProjectID", "rich_text": {"equals": project_id}}}
    res = requests.post(url, json=payload, headers=headers)
    results = res.json().get("results", [])
    return results[0] if results else None

def update_notion_page(page_id, data, github_url):
    """既存のNotionページに追記し、情報を最新化する"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    payload = {
        "children": [
            {"object": "block", "type": "divider", "divider": {}},
            {"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": f"🔄 更新記録 ({now})"}}]}},
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": data.get('insights', '-')}}]}}
        ]
    }
    requests.patch(url, json=payload, headers=headers)
    requests.patch(f"https://api.notion.com/v1/pages/{page_id}", json={"properties": {"Tools": {"rich_text": [{"text": {"content": data.get('tools', '-')}}]}, "GitHub": {"url": github_url}}}, headers=headers)
    return {"url": f"https://www.notion.so/{page_id.replace('-', '')}"}

def create_notion_page(data, github_url, project_id):
    """Notionに新規ページを作成する"""
    url = "https://api.notion.com/v1/pages"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID.replace("-", "")},
        "properties": {
            "Name": {"title": [{"text": {"content": data.get('title', 'Project')}}]},
            "ProjectID": {"rich_text": [{"text": {"content": project_id}}]},
            "Date": {"date": {"start": datetime.datetime.now().isoformat()}},
            "Tools": {"rich_text": [{"text": {"content": data.get('tools', '-')}}]},
            "GitHub": {"url": github_url}
        },
        "children": [
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "💡 失敗と工夫"}}]}},
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": data.get('insights', '-')}}]}}
        ]
    }
    res = requests.post(url, json=payload, headers=headers)
    return res.json()

def sync_github(project_id, input_file_path, insights):
    """GitHubに同期する (AIの要約をコミットメッセージに使用)"""
    repo = Repo(GITHUB_REPO_PATH)
    remote_url = f"https://{GITHUB_USER_NAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USER_NAME}/{os.path.basename(GITHUB_REPO_PATH)}.git"
    repo.remote('origin').set_url(remote_url)
    
    github_project_dir = Path(GITHUB_REPO_PATH) / "projects" / project_id
    if not github_project_dir.exists(): github_project_dir.mkdir(parents=True)
    
    # 既存フォルダ内の古い履歴をリネームして保存 (履歴を残す)
    history_file = github_project_dir / "latest_chat_history.md"
    if history_file.exists():
        old_history_name = f"chat_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        shutil.move(str(history_file), str(github_project_dir / old_history_name))

    # ファイルコピーの実行
    ignore_items = {'.git', 'record_agent.py', '.env', 'node_modules', 'setup_notion.py', 'record.bat', 'projects', '.agent', '.gitignore', 'inputs', 'run_output.txt', 'last_run.txt'}
    for item in os.listdir(GITHUB_REPO_PATH):
        if item in ignore_items or item.startswith('.'): continue
        s, d = Path(GITHUB_REPO_PATH) / item, github_project_dir / item
        if s.is_dir():
            if d.exists(): shutil.rmtree(d)
            shutil.copytree(s, d)
        elif s.is_file(): shutil.copy2(s, d)
    
    shutil.copy2(input_file_path, history_file)
    
    repo.git.add(A=True)
    # AIの要約（insights）をコミットメッセージにして「何をしたか」を可視化！
    commit_msg = f"Update: {insights[:50]}"
    repo.index.commit(commit_msg)
    repo.remote('origin').push()
    
    return f"https://github.com/{GITHUB_USER_NAME}/{os.path.basename(GITHUB_REPO_PATH)}/tree/master/projects/{project_id}"

def process_file(file_path):
    print(f"\n>>> 処理中: {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    data = analyze_markdown(content)
    # GitHub同期 (要約を渡す)
    github_url = sync_github(PROJECT_ID, file_path, data['insights'])
    
    # Notion同期
    existing_page = find_notion_page_by_id(PROJECT_ID)
    if existing_page:
        notion_res = update_notion_page(existing_page['id'], data, github_url)
        is_update = True
    else:
        notion_res = create_notion_page(data, github_url, PROJECT_ID)
        is_update = False
    
    notion_url = notion_res.get('url', 'Notion失敗')
    
    try:
        from tweepy import Client
        prefix = "【AI更新】" if is_update else "【AI開発】"
        tweet = f"{prefix}\n{data['title']}\n\n{data['x_summary']}\n\nNotion: {notion_url}\nGitHub: {github_url}\n#AIエージェント"
        Client(consumer_key=TWITTER_API_KEY, consumer_secret=TWITTER_API_SECRET, access_token=TWITTER_ACCESS_TOKEN, access_token_secret=TWITTER_ACCESS_SECRET).create_tweet(text=tweet[:280])
        print("✅ X投稿成功！")
    except Exception as e: print(f"❌ X投稿失敗: {e}")

    shutil.move(str(file_path), str(ARCHIVE_DIR / (datetime.datetime.now().strftime("%Y%m%d_%H%M%S_") + file_path.name)))
    print(f"--- 完了 (ID: {PROJECT_ID}) ---")

def main():
    if not INPUT_DIR.exists(): INPUT_DIR.mkdir()
    if not ARCHIVE_DIR.exists(): ARCHIVE_DIR.mkdir()
    md_files = list(INPUT_DIR.glob("*.md"))
    if not md_files: return
    for f in md_files: process_file(f)

if __name__ == "__main__": main()
