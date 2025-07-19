import requests
import feedparser
import os
from datetime import datetime
from transformers import pipeline
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# ================== Trending Topic Fetchers ==================
def fetch_reddit_headlines():
    url = "https://www.reddit.com/r/artificial/top/.json?t=day&limit=5"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    posts = res.json()["data"]["children"]
    return [p["data"]["title"] for p in posts]

def fetch_hackernews_headlines():
    top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:10]
    headlines = []
    for post_id in top_ids:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{post_id}.json").json()
        if item and "title" in item:
            if any(kw in item["title"].lower() for kw in ["ai", "machine learning", "artificial", "openai"]):
                headlines.append(item["title"])
    return headlines[:5]

def fetch_google_news():
    rss_url = "https://news.google.com/rss/search?q=ai+OR+artificial+intelligence+OR+machine+learning&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(rss_url)
    return [entry.title for entry in feed.entries[:5]]

def get_top_topic():
    headlines = fetch_reddit_headlines() + fetch_hackernews_headlines() + fetch_google_news()
    return headlines[0] if headlines else "Latest AI advancements in 2025"

# ================== Blog Generation ==================
def generate_blog(topic):
    print("🧠 Generating blog for topic:", topic)
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": [
            {
                "role": "user",
                "content": f"Write a 700-word AdSense-approved SEO blog on the topic: '{topic}'. Include a catchy title, introduction, at least three headings, and a conclusion. Use markdown with H1 and H2 headings. Ensure the content is 100% original."
            }
        ]
    }
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    return res.json()["choices"][0]["message"]["content"]

# ================== Self-Check for AdSense & Originality ==================
def check_adsense_and_originality(content):
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_KEY']}",
        "Content-Type": "application/json"
    }
    review_prompt = (
        "Analyze the following blog content.\n"
        "Answer only YES or NO to these 3 questions:\n"
        "1. Is this content original and not copied from any known sources?\n"
        "2. Does this content follow AdSense content policies (no violence, hate, illegal content, spam, or keyword stuffing)?\n"
        "3. Is this content grammatically correct and SEO friendly?\n\n"
        f"Content:\n{content}"
    )
    data = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": [{"role": "user", "content": review_prompt}]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

# ================== Plagiarism Check via API ==================
def check_plagiarism(content):
    print("🔍 Checking plagiarism...")
    headers = {
        "apikey": os.environ['PLAGIARISMDETECTOR_API_KEY'],
        "Content-Type": "application/json"
    }
    data = {
        "text": content,
        "language": "en"
    }
    response = requests.post("https://plagiarismdetector.net/api/v1/plagiarism", headers=headers, json=data)
    try:
        result = response.json()
        plagiarism_percent = result.get("plagiarism", 0)
        print(f"🔎 Plagiarism Detected: {plagiarism_percent}%")
        return plagiarism_percent <= 10
    except Exception as e:
        print("❌ Error in plagiarism check:", str(e))
        return False

# ================== LLM-Style Detection ==================
def check_llm_plagiarism(blog_content):
    print("🤖 Running LLM-based plagiarism check...")
    try:
        checker = pipeline("text-classification", model="roberta-base-openai-detector")
        result = checker(blog_content[:512])  # Limit to 512 tokens
        label = result[0]['label']
        score = result[0]['score']
        print(f"🔍 LLM Classifier Result: {label} ({score:.2f})")
        if label.lower() == "real" or score < 0.6:
            return True  # Considered original enough
        else:
            return False  # Too likely to be AI-generated or copied
    except Exception as e:
        print("❌ Error during LLM plagiarism check:", e)
        return False

# ================== Post to WordPress ==================
def post_to_wordpress(title, content):
    print("🚀 Posting to WordPress...")
    wp_url = "https://huztech.site/wp-json/wp/v2/posts"
    auth = (os.environ['WP_USERNAME'], os.environ['WP_APP_PASSWORD'])
    headers = {"Content-Type": "application/json"}
    data = {
        "title": title,
        "content": content,
        "status": "publish"
    }
    response = requests.post(wp_url, headers=headers, json=data, auth=auth)
    print("✅ Posted:", response.status_code)

# ================== Main Function ==================
def main():
    topic = get_top_topic()
    blog_content = generate_blog(topic)

    review_result = check_adsense_and_originality(blog_content)
    print("🧪 Self-check result:\n", review_result)

    if "YES" not in review_result.upper():
        print("❌ Content failed AdSense/self-check. Skipping.")
        return

    if not check_llm_plagiarism(blog_content):
        print("❌ LLM-style check failed (may be AI-generated or copied). Skipping post.")
        return

    title = f"{topic} – {datetime.now().strftime('%B %d, %Y')}"
    post_to_wordpress(title, blog_content)

# ================== Run the Agent ==================
if __name__ == "__main__":
    main()
