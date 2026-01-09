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

# 各種設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GITHUB_REPO_PATH = os.getenv("GITHUB_REPO_PATH")
GITHUB_USER_NAME = os.getenv("GITHUB_USER_NAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

def analyze_markdown(content):
    """LLMを使用してプロジェクト情報を抽出する"""
    clipped_content = content[-20000:] if len(content) > 20000 else content
    prompt = f"""
    以下のチャット履歴から、プロジェクトの情報を抽出してJSONで出力してください。
    1. title: プロジェクト名 (15文字以内)
    2. tools: 使用ツール (カンマ区切り)
    3. insights: 課題と工夫のまとめ
    4. x_summary: X用紹介文 (100文字以内)
    
    【チャット履歴】
    {clipped_content}
    """
    
    # OpenAI
    if OPENAI_API_KEY and OPENAI_API_KEY.strip().startswith("sk-"):
        try:
            print("Using OpenAI...")
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)
        except: pass

    # Gemini
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)
    for model_name in ['gemini-2.0-flash', 'gemini-1.5-flash']:
        try:
            print(f"Using Gemini ({model_name})...")
            res = client.models.generate_content(
                model=model_name, contents=prompt,
                config=types.GenerateContentConfig(response_mime_type='application/json')
            )
            data = json.loads(res.text)
            return data[0] if isinstance(data, list) else data
        except: continue
    raise Exception("AI解析に失敗しました。")

def create_notion_page(data, github_url):
    """Notionにページを作成する"""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID.replace("-", "")},
        "properties": {
            "Name": {"title": [{"text": {"content": data.get('title', 'Project')}}]},
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

def sync_github(project_name, local_dir):
    """GitHubに同期する"""
    repo = Repo(GITHUB_REPO_PATH)
    remote_url = f"https://{GITHUB_USER_NAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USER_NAME}/{os.path.basename(GITHUB_REPO_PATH)}.git"
    
    if 'origin' in repo.remotes: repo.remote('origin').set_url(remote_url)
    else: repo.create_remote('origin', remote_url)
    
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    clean_title = "".join(x for x in project_name if x.isalnum() or x in " -_").strip()
    github_project_dir = Path(GITHUB_REPO_PATH) / "projects" / f"{date_str}_{clean_title}"
    
    if not github_project_dir.exists(): github_project_dir.mkdir(parents=True)
    
    # ★重要：自分自身のプロジェクトフォルダやGitHub管理用ファイルを除外して無限ループを防ぐ
    ignore_items = {'.git', 'record_agent.py', '.env', 'node_modules', 'setup_notion.py', 'record.bat', 'projects', '.agent'}
    
    for item in os.listdir(local_dir):
        if item in ignore_items or item.startswith('.'): continue
        s, d = Path(local_dir) / item, github_project_dir / item
        if s.is_dir():
            if d.exists(): shutil.rmtree(d)
            shutil.copytree(s, d)
        else: shutil.copy2(s, d)
    
    # 初回プッシュのための設定
    repo.git.add(A=True)
    repo.index.commit(f"Add: {project_name}")
    try:
        current_branch = repo.active_branch.name
        repo.git.push('--set-upstream', 'origin', current_branch)
    except:
        repo.remote('origin').push()
    
    return f"https://github.com/{GITHUB_USER_NAME}/{os.path.basename(GITHUB_REPO_PATH)}/tree/main/projects/{date_str}_{clean_title}"

def post_to_x(data, notion_url, github_url):
    """Xに投稿する"""
    client = tweepy.Client(
        consumer_key=TWITTER_API_KEY, consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN, access_token_secret=TWITTER_ACCESS_SECRET
    )
    text = f"【AI開発記録】\n{data.get('title')}\n\n{data.get('x_summary')}\n\nNotion: {notion_url}\nGitHub: {github_url}\n#AIエージェント"
    client.create_tweet(text=text)

def main():
    print("--- 処理開始 ---")
    with open("AI Agent Activity Automation.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    data = analyze_markdown(content)
    print(f"タイトル: {data['title']}")
    
    github_url = sync_github(data['title'], os.getcwd())
    print(f"GitHub: {github_url}")
    
    notion_res = create_notion_page(data, github_url)
    notion_url = notion_res.get('url', 'Notion失敗')
    print(f"Notion: {notion_url}")
    if 'object' in notion_res and notion_res['object'] == 'error':
        print(f"Notionエラー詳細: {notion_res['message']}")
    
    try:
        post_to_x(data, notion_url, github_url)
        print("X投稿完了！")
    except Exception as e:
        print(f"X投稿失敗: {e}")

if __name__ == "__main__":
    main()
