# Backend for Latest News Agent

## Run

- Create and populate `.env` in `/workspace/ai-news-agent` or `/workspace/ai-news-agent/backend` with:

```
OPENAI_API_KEY=your_openai_key
EXA_API_KEY=your_exa_key
```

- Install deps:

```
pip install -r backend/requirements.txt
```

- Start server (port 12001):

```
uvicorn app.main:app --host 0.0.0.0 --port 12001 --reload
```

- Health check: `GET http://localhost:12001/health`
