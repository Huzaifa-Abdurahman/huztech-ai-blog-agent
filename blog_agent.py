import requests
from datetime import datetime
import random

# Trending AI topic (can use Reddit API, simplified here)
topics = [
    "Latest breakthroughs in AI models",
    "Open-source LLMs like Mistral and LLAMA",
    "Impact of Generative AI on Software Engineering",
    "Top AI tools in 2025"
]
topic = random.choice(topics)

# Step 1: Generate blog via OpenRouter (free LLM)
def generate_blog(topic):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer YOUR_OPENROUTER_KEY",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/mixtral-8x7b-instruct",
            "messages": [
                {"role": "user", "content": f"Write a 600-word AdSense-friendly SEO blog post about: {topic}. Use H1, H2, conclusion, and make it unique."}
            ]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

# Step 2: Post to WordPress
def post_to_wordpress(title, content):
    wp_url = "https://huztech.site/wp-json/wp/v2/posts"
    auth = ("YOUR_WP_USERNAME", "YOUR_APP_PASSWORD")  # From WP plugin
    headers = {"Content-Type": "application/json"}
    data = {
        "title": title,
        "content": content,
        "status": "publish"
    }
    response = requests.post(wp_url, json=data, auth=auth, headers=headers)
    print("✅ Posted to WordPress:", response.status_code)

# Main task
title = f"{topic} - {datetime.now().strftime('%B %d, %Y')}"
content = generate_blog(topic)
post_to_wordpress(title, content)
