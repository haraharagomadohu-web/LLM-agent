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
    """環境変数を取得し、余計な空白やクォートを取り除く"""
    val = os.getenv(key)
    if val:
        return val.strip().strip("'").strip('"')
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

INPUT_DIR = Path("inputs")
ARCHIVE_DIR = INPUT_DIR / "archived"

def analyze_markdown(content):
    """LLMを使用してプロジェクト情報を抽出する"""
    clipped_content = content[-15000:] if len(content) > 15000 else content
    prompt = f"""
    以下のチャット履歴からプログラミングプロジェクトの要約を生成してください。
    【出力形式】必ず以下のキーを持つJSON
    - title: プロジェクト名 (15文字以内)
    - tools: 言語/ツール (カンマ区切り)
    - insights: 失敗と工夫の要約
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
        print(f"Gemini解析エラー (OpenAIを試行します): {e}")
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e2:
            raise Exception(f"AI解析に失敗しました: {e2}")

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

def sync_github(project_name, input_file_path):
    """GitHubに同期する"""
    repo = Repo(GITHUB_REPO_PATH)
    remote_url = f"https://{GITHUB_USER_NAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USER_NAME}/{os.path.basename(GITHUB_REPO_PATH)}.git"
    repo.remote('origin').set_url(remote_url)
    
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    clean_title = "".join(x for x in project_name if x.isalnum() or x in " -_").strip()
    folder_name = f"{date_str}_{clean_title}"
    github_project_dir = Path(GITHUB_REPO_PATH) / "projects" / folder_name
    
    if not github_project_dir.exists(): github_project_dir.mkdir(parents=True)
    
    # 既存ファイルをコピー
    ignore_items = {'.git', 'record_agent.py', '.env', 'node_modules', 'setup_notion.py', 'record.bat', 'projects', '.agent', '.gitignore', 'inputs'}
    for item in os.listdir(GITHUB_REPO_PATH):
        if item in ignore_items or item.startswith('.'): continue
        s, d = Path(GITHUB_REPO_PATH) / item, github_project_dir / item
        if s.is_dir():
            if d.exists(): shutil.rmtree(d)
            shutil.copytree(s, d)
        elif s.is_file():
            shutil.copy2(s, d)
    
    # チャット履歴を専用名でコピー
    shutil.copy2(input_file_path, github_project_dir / "chat_history.md")
    
    # README作成
    with open(github_project_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(f"# {project_name}\n\n## 開発記録\n自動保存されたプロジェクトです。\n\n## 履歴\n[chat_history.md](./chat_history.md)")

    repo.git.add(A=True)
    repo.index.commit(f"Record: {project_name}")
    repo.remote('origin').push()
    
    return f"https://github.com/{GITHUB_USER_NAME}/{os.path.basename(GITHUB_REPO_PATH)}/tree/master/projects/{folder_name}"

def post_to_x(data, notion_url, github_url):
    """Xに投稿する"""
    client = tweepy.Client(
        consumer_key=TWITTER_API_KEY, consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN, access_token_secret=TWITTER_ACCESS_SECRET
    )
    title = data.get('title', '新プロジェクト')
    summary = data.get('x_summary', 'AI活用で開発中！')
    text = f"【AI開発記録】\n{title}\n\n{summary}\n\nNotion: {notion_url}\nGitHub: {github_url}\n#AIエージェント"
    
    # 文字数制限対策 (Xは約140文字/全角280バイト制限)
    if len(text) > 280: text = text[:277] + "..."
    
    print(f"--- Xに送信中... ---\n{text}")
    client.create_tweet(text=text)

def process_file(file_path):
    print(f"\n>>> 処理中: {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    data = analyze_markdown(content)
    print(f"タイトル: {data['title']}")
    
    github_url = sync_github(data['title'], file_path)
    print(f"GitHub: {github_url}")
    
    notion_res = create_notion_page(data, github_url)
    notion_url = notion_res.get('url', 'Notion失敗')
    print(f"Notion: {notion_url}")
    
    try:
        post_to_x(data, notion_url, github_url)
        print("✅ X投稿成功！")
    except Exception as e:
        print(f"❌ X投稿失敗: {e}")
        # 詳細なデバッグ情報を表示
        if "403" in str(e):
            print("💡 403エラーの原因候補：")
            print(" (1) 同じ内容を短時間に連投した（スパム防止）")
            print(" (2) アプリの権限設定後、キーの再生成（Regenerate）を忘れている")
            print(" (3) 1日の投稿上限に達した")

    # アーカイブ
    archive_path = ARCHIVE_DIR / (datetime.datetime.now().strftime("%Y%m%d_%H%M%S_") + file_path.name)
    shutil.move(str(file_path), str(archive_path))
    print(f"--- 完了 (アーカイブ: {archive_path.name}) ---")

def main():
    if not INPUT_DIR.exists(): INPUT_DIR.mkdir()
    if not ARCHIVE_DIR.exists(): ARCHIVE_DIR.mkdir()
    md_files = list(INPUT_DIR.glob("*.md"))
    if not md_files:
        print("処理待ちのファイルが inputs フォルダにありません。")
        return
    for f in md_files:
        try:
            process_file(f)
        except Exception as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    main()
