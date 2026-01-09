import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

# .env から読み込み
ak = os.getenv("TWITTER_API_KEY")
as_ = os.getenv("TWITTER_API_SECRET")
at = os.getenv("TWITTER_ACCESS_TOKEN")
ats = os.getenv("TWITTER_ACCESS_SECRET")

print("--- X Auth Debug ---")
print(f"API Key (Consumer Key) exists: {bool(ak)}")
print(f"API Key Secret exists: {bool(as_)}")
print(f"Access Token exists: {bool(at)}")
print(f"Access Token Secret exists: {bool(ats)}")

try:
    client = tweepy.Client(
        consumer_key=ak,
        consumer_secret=as_,
        access_token=at,
        access_token_secret=ats
    )
    
    # テスト投稿
    print("\nテスト投稿を送信中...")
    response = client.create_tweet(text="AI自動化システムからのテスト投稿です。 #Test")
    print("✅ 成功しました！")
    print(f"Tweet ID: {response.data['id']}")

except tweepy.TweepyException as e:
    print("\n❌ エラーが発生しました:")
    print(e)
    print("\n💡 ヒント:")
    print("1. 403 Forbidden の場合、権限が 'Read and Write' に設定されていないか、設定後に鍵を再生成(Regenerate)していません。")
    print("2. OAuth 1.0a Settings が有効になっているか確認してください。")
except Exception as e:
    print(f"\n予期せぬエラー: {e}")
