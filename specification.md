# AIエージェント活動記録・公開自動化システム 仕様書

## 1. 目的
毎日作成するAIエージェントの開発情報を、最小限の手間で「管理・俯瞰（Notion）」「資材管理（GitHub）」「発信（X/Twitter）」の3箇所へ同期・自動公開するための自動化システムを構築する。
特にNotionを「世界地図」として位置づけ、過去の全プロジェクトを網羅的に把握可能にする。

## 2. システム概要
Pythonスクリプトを実行し、プロジェクトディレクトリ内の特定のMarkdownファイルを読み取って、以下の処理を自動で完結させる。

1. **Notion**: 「世界地図」データベースへ新規ページを追加。公開設定されたデータベースにより自動でWeb公開される。
2. **GitHub**: プロジェクトフォルダ（全ファイル）を特定リポジトリにコミット・プッシュ。
3. **X (Twitter)**: APIを使用して、リンク付きのサマリーを自動ポスト。

## 3. ワークフロー（利用シーン）
1. ユーザーが開発プロジェクトフォルダ内に `AI Agent Activity Automation.md` という名称でチャット履歴等を保存する。
2. ターミナルで `python record_agent.py` を実行。
3. スクリプトが自動的に同フォルダ内の `AI Agent Activity Automation.md` を読み込む。
4. **自動処理開始**:
   - LLMがファイル内容を解析し、「ターゲット名」「使用ツール」「失敗と工夫（サマリー）」を抽出。
   - `projects/YYYYMMDD_プロジェクト名/` フォルダをGitHubリポジトリ内に作成し、フォルダ内の全ファイルをプッシュ。
   - Notionデータベースに新規ページを作成し、情報を記録。
   - **X (Twitter) APIを使用して自動投稿。** （Notion公開URL、GitHub URL、失敗と工夫を含む）
5. 全処理完了の通知。

## 4. 機能詳細

### 4.1. データ解析機能（LLM）
- **役割**: `AI Agent Activity Automation.md` から各プラットフォーム用の情報を抽出。
- **動作**: OpenAI API (gpt-4o-mini等) を使用し、タイトル、使用ツール、X投稿用サマリー、詳細な失敗と工夫を抽出。

### 4.2. Notion 連携機能（自動記録・公開）
- **動作**: 
  - 取得した情報を元に、Notionデータベースへ新しいページを追加。
  - **ページ内構成**:
    - **システム仕様書**: 本システムの `specification.md` の内容を転記。
    - **開発ログ**: LLMが抽出した詳細な「失敗と工夫」、および元のチャット履歴全文。
- **公開について**: データベース自体をWeb公開設定にすることで、各ページも自動的に公開される。

### 4.3. GitHub 連携機能（プロジェクト同期）
- **動作**:
  - 実行ディレクトリ内の全ファイルを、GitHubリポジトリの `projects/YYYYMMDD_プロジェクト名/` 以下に配置。
  - GitPythonにより `add`, `commit`, `push` を自動実行。

### 4.4. X (Twitter) 連携機能（完全自動投稿）
- **動作**: 
  - `tweepy` ライブラリを使用。
  - **ポスト内容例**:
    ```text
    【AIエージェント開発記録】
    [プロジェクト名] を作成しました！
    
    [失敗と工夫の要約]
    
    詳細(Notion): [Notion公開URL]
    コード(GitHub): [GitHub URL]
    #AIエージェント #自動化
    ```

## 5. 技術スタック
- **言語**: Python 3.10+
- **ライブラリ**:
  - `openai`: 知見の抽出・サマリー生成用
  - `requests`: Notion API操作用
  - `GitPython`: GitHub操作用
  - `tweepy`: X (Twitter) API操作用
  - `python-dotenv`: 環境変数管理用

## 6. セットアップ・構成
- `.env`: 以下の機密情報を保持。
  - `OPENAI_API_KEY`
  - `NOTION_TOKEN` / `NOTION_DATABASE_ID`
  - `GITHUB_REPO_PATH` / `GITHUB_USER_NAME`
  - `TWITTER_API_KEY` / `TWITTER_API_SECRET`
  - `TWITTER_ACCESS_TOKEN` / `TWITTER_ACCESS_SECRET`

## 7. 非機能要件・セキュリティ
- APIキーなどの機密情報は `.env` に格納し、`.gitignore` で除外。
- エラーハンドリング（API失敗時のログ出力、再試行等）。
