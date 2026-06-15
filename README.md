# Groww Pulse

Groww Pulse is an automated, AI-driven App Review Intelligence pipeline. It completely automates the tedious process of reading through hundreds of raw Google Play Store reviews, identifying emerging pain points, and delivering executive-ready reports directly into Google Docs.

![Groww Pulse Dashboard](https://raw.githubusercontent.com/Keerttik/Groww-Pulse/main/web/public/favicon.svg)

## 🚀 How It Works (The Pipeline)

Groww Pulse operates via an ephemeral Python background task that triggers periodically (or manually via the dashboard):

1. **Scraping (MCP Server):** A dedicated Play Store MCP (Model Context Protocol) Server fetches the latest reviews from the Google Play Store.
2. **PII Scrubbing:** Raw reviews are immediately scrubbed of Personally Identifiable Information before being sent anywhere.
3. **Embeddings:** The reviews are converted into dense vector embeddings locally using the open-source `BAAI/bge-small-en-v1.5` model.
4. **Clustering (UMAP + HDBSCAN):** The high-dimensional vectors are reduced and clustered to group semantically similar complaints and praises together.
5. **AI Summarization (Groq LLaMA-3):** Each dense cluster is passed to the blazing-fast Groq LLaMA-3.3-70b model, which identifies the core Theme, extracts exactly 5 representative real-user quotes, and formulates an actionable product idea.
6. **Delivery:** The final structured "Pulse Report" is appended directly to a shared Google Doc, and the run statistics are saved to a local SQLite database.

## 🏗️ Architecture

The project is structured as a monolithic repository that houses both the intelligent Python backend and the React frontend dashboard.

* `/agent` - The core AI pipeline (`orchestrator.py`, clustering algorithms, LLM interactions, Google Docs delivery).
* `/play_store_mcp` - A standalone Python MCP server that securely interfaces with the Google Play Store.
* `/web` - A Vite + React dashboard that polls the backend for historical runs and provides a UI to trigger manual runs.
* `Dockerfile` & `railway.json` - Production configuration for deploying the entire application to Railway.

## 🛠️ Tech Stack

* **Backend:** FastAPI, Python, SQLite
* **AI/ML:** Sentence-Transformers, UMAP, HDBSCAN, Groq API (LLaMA-3.3-70b-versatile)
* **Frontend:** React, Vite, Vanilla CSS
* **Deployment:** Docker, Railway Cloud

## ⚙️ Environment Setup

To run Groww Pulse locally or deploy it to the cloud, you will need to set the following environment variables in your `.env` file:

```env
# Groq API Key for the LLaMA summarization model
GROQ_API_KEY=gsk_your_key_here

# Security Key to authenticate communication between the Orchestrator and the MCP Server
MCP_API_SECRET_KEY=super_secret_internal_key

# The ID of the Google Doc where reports should be delivered 
# (Found in the URL: https://docs.google.com/document/d/<THIS_ID>/edit)
GOOGLE_DOC_ID=1x2y3z...

# REST API Configuration (used for Docker/Railway deployments)
REST_SERVER_URL=http://localhost:8000
PORT=8000
DATA_DIR=/data
```

## ☁️ Deployment

Groww Pulse is fully containerized and configured for 1-click deployment on **Railway**. 

1. Push this repository to GitHub.
2. Create a new Railway project and connect your GitHub repo.
3. Railway will automatically detect the `Dockerfile` and `railway.json`.
4. Add a Persistent Volume to your Railway service and mount it to `/data` so your SQLite database (`/data/pulse.db`) survives deployments.
5. Add the Environment Variables listed above in the Railway dashboard.
6. The frontend dashboard will be available at your Railway public domain!

## 🔄 How to re-run for a new week

1. Open your hosted React Dashboard.
2. Click the large green **"RUN PULSE NOW & FETCH INSIGHTS"** button.
3. The backend will automatically compute the current ISO week, fetch the latest reviews, generate the themes, and upload the final 1-page note to the shared Google Doc.
4. You can download the raw `reviews_export.csv` from the `/data` volume in Railway for debugging.

## 📖 Theme Legend

The AI pipeline uses Unsupervised Machine Learning (HDBSCAN) to discover themes organically rather than forcing reviews into hardcoded buckets. However, the LLM is instructed to classify the sentiment and nature of the themes. Typical themes include:
- 🔴 **Negative Sentiment:** Bugs, crashes, login issues, or poor customer support experiences.
- 🟡 **Neutral Sentiment:** Feature requests, general observations, or onboarding questions.
- 🟢 **Positive Sentiment:** Praise for UI/UX, successful trades, or general app satisfaction.
