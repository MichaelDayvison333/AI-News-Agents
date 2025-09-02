# Latest News Agent

A minimal web app with Next.js frontend and Python FastAPI backend. The AI agent gathers user preferences, fetches latest news with Exa API, and summarizes them with OpenAI.

## Features

- Simple chat UI with conversation list and input
- Visual checklist for five preferences (tone, format, language, interaction, topics)
- Backend uses raw OpenAI tool calling to decide when to use tools:
  - `exa_news_fetch` to search and retrieve news
  - `summarize_news` to summarize results
- CORS enabled; runs on required ports

## Architecture

- Frontend: Next.js 14, pages router
- Backend: FastAPI, uvicorn

## Prerequisites

- Node.js 18+
- Python 3.10+
- API keys: `OPENAI_API_KEY`, `EXA_API_KEY`

## Local Setup

1. Install backend deps and run backend (port 12001):

```
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 12001 --reload
```

2. Install frontend deps and run frontend (port 12000):

```
cd frontend
npm install
NEXT_PUBLIC_BACKEND_URL=http://localhost:12001 npm run dev
```

Open http://localhost:12000

## Environment (this assessment)

- Frontend host: https://work-1-gkenubufgwosjdnq.prod-runtime.all-hands.dev (port 12000)
- Backend host:  https://work-2-gkenubufgwosjdnq.prod-runtime.all-hands.dev (port 12001)

Run backend bound to 0.0.0.0:12001 and frontend on 0.0.0.0:12000. Set NEXT_PUBLIC_BACKEND_URL to the backend host URL when running dev.

## Notes & Assumptions

- OpenAI tool calling is implemented via raw HTTP to `/v1/chat/completions` with `tools`. We execute tools server-side and stream results through iterative calls until the model returns a final message.
- If `OPENAI_API_KEY` is not set, backend falls back to a simple heuristic: it asks onboarding questions and uses Exa fetch + a simple summarizer as fallback.
- Preference extraction from free text is minimal; users can set them directly in the UI using `key: value` commands. A production version would use structured extraction.

## Deployment

This repo is designed for local run. To deploy, host the backend and frontend, setting the correct environment variables.
