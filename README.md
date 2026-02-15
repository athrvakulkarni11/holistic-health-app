# Holistic Health AI Platform 🏥✨

A premium, AI-powered healthcare analytics platform that interprets biomarker data to provide personalized health suggestions.

## 🌟 Features

-   **AI Analysis**: Uses **Groq LLM** (Llama 3) for deep medical insights.
-   **Knowledge Base**: RAG (Retrieval Augmented Generation) with a curated medical vector database (**ChromaDB**).
-   **Web Search**: Real-time validation using **DuckDuckGo** for the latest clinical research.
-   **Premium UI**: Modern, glassmorphism-based design with smooth animations.
-   **Privacy Focused**: Data is processed locally or via secure API calls; no persistent user storage (MVP).

## 🚀 Quick Start

### 1. Prerequisites
-   Python 3.10+
-   A [Groq API Key](https://console.groq.com/) (Free)

### 2. Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
1.  Rename `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```
2.  Open `.env` and add your Groq API key:
    ```env
    GROQ_API_KEY=gsk_...
    ```

### 4. Run the App
```bash
python main.py
```

Visit **[http://localhost:8050](http://localhost:8050)** in your browser.

## 🏗 Architecture
-   **Backend**: FastAPI
-   **Frontend**: Vanilla JS + CSS3 (Glassmorphism)
-   **Database**: ChromaDB (Vector Store for Knowledge Base)
-   **AI Engine**: Groq (Llama 3 70B) + LangChain
-   **Search**: DuckDuckGo API

## 🧪 Testing
Click the **"Fill Demo Data"** button on the form to instantly populate a sample high-risk profile (high cholesterol, pre-diabetic, low vitamin D) to see the analysis engine in action.
