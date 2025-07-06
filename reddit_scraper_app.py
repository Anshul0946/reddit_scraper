import streamlit as st
import praw
import json
import os

# ==== Reddit Auth ====
reddit = praw.Reddit(
    client_id='VD0DaZJV-rGRXLzbV_pxPA',
    client_secret='qGD-7qsxmMEbfeG-CKKmwoAlWBsrDg',
    user_agent='RedditScraper by u/hexverse'
)

# ==== Helper to recursively get all comments + replies ====
def get_comment_tree(comment):
    comment_data = {
        "author": str(comment.author),
        "body": comment.body,
        "score": comment.score,
        "replies": []
    }
    if hasattr(comment, "replies"):
        for reply in comment.replies:
            comment_data["replies"].append(get_comment_tree(reply))
    return comment_data

# ==== Main scraper logic ====
def reddit_scraper(subreddits, query, time_filter, post_limit):
    all_results = []

    for subreddit_name in subreddits:
        st.write(f"🔍 Searching r/{subreddit_name} for '{query}' in past {time_filter}...")

        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts = subreddit.search(query, sort="new", time_filter=time_filter, limit=post_limit)

            for submission in posts:
                submission.comments.replace_more(limit=None)

                post_comments = [get_comment_tree(comment) for comment in submission.comments]

                all_results.append({
                    "subreddit": subreddit_name,
                    "title": submission.title,
                    "author": str(submission.author),
                    "url": f"https://www.reddit.com{submission.permalink}",
                    "created_utc": submission.created_utc,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "body": submission.selftext,
                    "comments": post_comments
                })

        except Exception as e:
            st.error(f"❌ Error with r/{subreddit_name}: {e}")

    return all_results

# ==== Streamlit UI ====
st.title("📊 Reddit Post & Comment Scraper")

st.markdown("This app lets you scrape Reddit posts & full comment threads by keyword and subreddit filters.")

# 🎯 User input: keyword
search_query = st.text_input("🔎 Enter your keyword or advanced Reddit query", "biggest challenge")

# 📚 Subreddits
all_subreddits = ["ecommerce", "shopify", "smallbusiness", "entrepreneur", "marketing", "ecommercemarketing"]
selected_subreddits = st.multiselect("📚 Select subreddits to search in:", all_subreddits, default=["ecommerce"])

# 🕒 Time filter
time_filter = st.selectbox("⏱️ Select time filter:", ["hour", "day", "week", "month", "year", "all"], index=4)

# 🔢 Number of posts
post_limit = st.slider("📦 How many posts per subreddit?", min_value=1, max_value=100, value=20)

# 📁 Output filename
filename = st.text_input("💾 Enter filename to save (e.g. reddit_output.json):", "reddit_output.json")

# 🚀 Run scraper
if st.button("🚀 Run Scraper"):
    if not selected_subreddits or not filename:
        st.error("⚠️ Please select at least one subreddit and specify a valid filename.")
    else:
        with st.spinner("🔄 Scraping Reddit..."):
            results = reddit_scraper(selected_subreddits, search_query, time_filter, post_limit)

            # Save to file
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4, ensure_ascii=False)

        st.success(f"✅ Scraped {len(results)} posts! Saved to `{filename}`")

        # Optional: show download link
        with open(filename, "rb") as f:
            st.download_button("⬇️ Download JSON file", data=f, file_name=filename, mime="application/json")
