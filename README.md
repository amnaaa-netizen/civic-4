# 🏙️ Civic Issue Reporter Pro

AI-powered civic issue reporting app — snap a photo, AI classifies it, and it's auto-routed to the correct department.

## ✨ Features

- 🤖 **AI Image Classification** (CLIP zero-shot model)
- ⚡ **Auto Severity Detection**
- 💾 **SQLite Database** (permanent storage)
- 🔁 **Duplicate Detection** (same issue nearby auto-upvotes)
- 👍 **Upvote System** (crowd priority)
- 🛠️ **Admin Panel** (resolve reports)
- 📊 **Live Dashboard** with charts + map
- 📥 **CSV Export**

## 🚀 Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. New app → select repo → main file: `app.py`
4. Deploy 🎉

## 🧑‍💻 Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
