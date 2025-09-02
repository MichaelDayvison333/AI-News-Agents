# Latest News Agent

A web-based chat application that delivers curated, up-to-date news summaries tailored to each user’s preferences. The frontend (Next.js) provides a clean chat UI and a live preferences checklist. The backend (FastAPI) orchestrates raw OpenAI tool-calling with two tools:
- Exa News Fetcher: retrieves the latest articles using the Exa API
- News Summarizer: summarizes articles in the user’s requested tone, format, language, and interaction style

## Rust/cargo reference
- Not required for normal development and running this project.
- Why you might see Rust mentioned: Next.js uses SWC/Turbopack (written in Rust), and some dependencies may print notes that reference Rust. This is expected and does not require action.
- When you might need it: Only if your local setup compiles native Node modules and prompts for cargo.
  - macOS/Linux:
    - curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    - source "$HOME/.cargo/env"
    - rustc --version && cargo --version
  - Windows:
    - Install via https://rustup.rs (stable toolchain by default)
- For this assessment environment, you do not need to install Rust/cargo.

## Live environment (assessment)
- Frontend (port 12000): https://work-1-gkenubufgwosjdnq.prod-runtime.all-hands.dev
- Backend (port 12001):  https://work-2-gkenubufgwosjdnq.prod-runtime.all-hands.dev

Ensure the backend runs on 0.0.0.0:12001 and the frontend on 0.0.0.0:12000. Set `NEXT_PUBLIC_BACKEND_URL` to the backend URL when running the frontend in dev.

## Features
- Chat UI with conversation history and input box
- Visual checklist for five preferences (tone, format, language, interaction, topics)
- “key: value” commands in chat (e.g., `tone: formal`) that update preferences immediately
- Raw OpenAI tool calling (no wrappers):
  - `save_preferences` to structure updates
  - `exa_news_fetch` to search and retrieve news
  - `summarize_news` to summarize results
- Fallback behavior when keys are missing or OpenAI quota is exceeded
- CORS/iframe friendly

## Architecture
- Frontend: Next.js 14 (pages router)
- Backend: FastAPI + Uvicorn
- Tool flow on the backend:
  1. Collect missing preferences (ask one at a time)
  2. On request, call `exa_news_fetch` then `summarize_news`
  3. Return assistant message and updated preferences to the UI

## Tech stack
- Frontend: Next.js 14, React 18, TypeScript
- Backend: FastAPI, Uvicorn, Pydantic, Requests, python-dotenv
- APIs: OpenAI (chat.completions), Exa (search)

## Prerequisites
- Node.js 18+
- Python 3.10+
- API keys: `EXA_API_KEY` (required for live fetch), `OPENAI_API_KEY` (optional; enables high‑quality summaries and tool-calling)

## Getting API keys
- Exa: https://exa.ai → Dashboard → API Keys → Create key → copy value
- OpenAI: https://platform.openai.com → View API keys → Create new secret key

Add to `backend/.env` (dotenv auto-loads on backend start):
```
EXA_API_KEY=your_exa_key
OPENAI_API_KEY=your_openai_key   # optional
```

## Local setup
1) Backend (port 12001)
```
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 12001 --reload
```
Health check: http://localhost:12001/health → {"status":"ok"}

2) Frontend (port 12000)
```
cd frontend
npm install
NEXT_PUBLIC_BACKEND_URL=http://localhost:12001 npm run dev
```
Open http://localhost:12000

## Using the app
1) Provide preferences via chat (examples):
- `tone: formal`
- `format: bullet points`
- `language: English`
- `interaction: concise`
- `topics: technology, ai`

2) Ask for news:
- “Give me the latest on technology.”

The checklist updates as each preference is provided. With both keys set, you’ll receive linked, formatted summaries. Without `OPENAI_API_KEY`, the app uses a basic local summarizer; without `EXA_API_KEY`, fetching will return an explicit Exa error.

## Backend API
- POST `/chat`
  - Request: `{ messages: [{role, content}], preferences: { tone?, format?, language?, interaction?, topics? } }`
  - Response: `{ messages: [...], updatedPreferences: {...} }`
- GET `/health`
  - Response: `{ "status": "ok" }`

## Troubleshooting
- “Error contacting backend”
  - Frontend cannot reach backend. Verify backend is running on port 12001 and `NEXT_PUBLIC_BACKEND_URL` matches.
- “OpenAI error 429: insufficient_quota”
  - Add billing/increase quota in the OpenAI dashboard, or comment out `OPENAI_API_KEY` to use the fallback summarizer.
- “Exa error: Missing EXA_API_KEY”
  - Add `EXA_API_KEY` to `backend/.env` and restart the backend.
- OpenAI 400 errors
  - The backend now surfaces exact errors to chat; if you see a schema/model error, share it for precise guidance.

## Notes & decisions
- OpenAI integration uses raw HTTP with tool definitions; no third‑party wrappers
- Preferences are supplied from the client and also handled via a `save_preferences` tool
- Styling is lightweight and focused on clarity; CORS is permissive for ease of embedding

## Deployment
Host the backend and frontend with the same env vars. Ensure the frontend uses `NEXT_PUBLIC_BACKEND_URL` pointing to the backend. Keep `.env` files out of version control.
