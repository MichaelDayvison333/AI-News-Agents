import os
import json
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EXA_API_KEY = os.getenv("EXA_API_KEY", "")

app = FastAPI()

# Allow CORS from anywhere for demo purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data models ---
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    preferences: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    messages: List[Message]
    updatedPreferences: Dict[str, Any]

# --- Tool functions ---

def exa_news_fetch(topic: str, num_results: int = 5) -> Dict[str, Any]:
    if not EXA_API_KEY:
        return {"error": "Missing EXA_API_KEY"}
    url = "https://api.exa.ai/search"
    payload = {
        "query": f"latest news about {topic}",
        "numResults": num_results,
        "text": True,
        "summary": {"query": "Summarize the article in 3 bullet points"}
    }
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("results", [])[:num_results]:
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "summary": item.get("summary"),
                "publishedDate": item.get("publishedDate")
            })
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}


def summarize_news(items: List[Dict[str, Any]], style: str = "concise", format_: str = "bullet points", language: str = "English", tone: str = "neutral") -> Dict[str, Any]:
    # Use OpenAI Responses API to summarize
    if not OPENAI_API_KEY:
        # Fallback simple summarization
        bullets = []
        for it in items:
            bullets.append(f"- {it.get('title')}: {it.get('summary') or 'No summary available'}")
        return {"summary": "\n".join(bullets)}

    prompt = {
        "type": "text",
        "text": (
            "You are a helpful assistant summarizing news articles.\n"
            f"Tone: {tone}. Interaction style: {style}. Format: {format_}. Language: {language}.\n"
            "Summarize the following news items with citations to their URLs. Keep it factual and recent.\n"
            + json.dumps(items)
        )
    }

    try:
        # Raw OpenAI HTTP call
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "input": [prompt],
        }
        resp = requests.post("https://api.openai.com/v1/responses", headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text_out = data.get("output", [{}])[0].get("content", [{}])[0].get("text")
        if not text_out:
            # try alt path
            text_out = data.get("choices", [{}])[0].get("message", {}).get("content")
        return {"summary": text_out or ""}
    except Exception as e:
        bullets = []
        for it in items:
            bullets.append(f"- {it.get('title')}: {it.get('summary') or 'No summary available'}")
        return {"summary": "\n".join(bullets), "warning": str(e)}

# --- Raw tool-calling with OpenAI ---

def openai_chat_with_tools(messages: List[Dict[str, str]], preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use OpenAI tool calling: define tools: exa_news_fetch, summarize_news, save_preferences.
    We'll implement the tool execution in-process and feed results back with tool messages.
    """
    if not OPENAI_API_KEY:
        # Offline heuristic bot: ask onboarding questions until preferences filled, then fetch via Exa and summarize.
        updated = {**preferences}
        questions = [
            ("tone", "Preferred Tone of Voice (e.g., formal, casual, enthusiastic)?"),
            ("format", "Preferred Response Format (e.g., bullet points, paragraphs)?"),
            ("language", "Language Preference (e.g., English, Spanish)?"),
            ("interaction", "Interaction Style (e.g., concise, detailed)?"),
            ("topics", "Preferred News Topics (e.g., technology, sports, politics)?"),
        ]
        for key, q in questions:
            if not updated.get(key):
                return {
                    "assistant_message": q,
                    "preferences": updated,
                }
        # all set, attempt fetch + summarize
        topics = updated.get("topics")
        result_texts = []
        if isinstance(topics, list):
            tlist = topics
        else:
            tlist = [topics]
        for topic in tlist:
            exa = exa_news_fetch(topic, 5)
            if "results" in exa:
                summ = summarize_news(exa["results"], updated.get("interaction", "concise"), updated.get("format", "bullet points"), updated.get("language", "English"), updated.get("tone", "neutral"))
                result_texts.append(f"Topic: {topic}\n{summ.get('summary')}")
            else:
                result_texts.append(f"Topic: {topic}\nExa error: {exa.get('error')}")
        return {
            "assistant_message": "\n\n".join(result_texts),
            "preferences": updated,
        }

    # Prepare tools schema
    tools = [
        {
            "type": "function",
            "function": {
                "name": "exa_news_fetch",
                "description": "Fetch latest news articles for a topic using Exa API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "num_results": {"type": "integer", "minimum": 1, "maximum": 10}
                    },
                    "required": ["topic"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "summarize_news",
                "description": "Summarize a list of news items using OpenAI, respecting preferences",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": ["string", "null"]},
                                    "url": {"type": ["string", "null"]},
                                    "summary": {"type": ["string", "null"]},
                                    "publishedDate": {"type": ["string", "null"]}
                                },
                                "additionalProperties": True
                            }
                        },
                        "style": {"type": "string"},
                        "format_": {"type": "string"},
                        "language": {"type": "string"},
                        "tone": {"type": "string"}
                    },
                    "required": ["items"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "save_preferences",
                "description": "Save user preferences (tone, format, language, interaction, topics).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tone": {"type": "string"},
                        "format": {"type": "string"},
                        "language": {"type": "string"},
                        "interaction": {"type": "string"},
                        "topics": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]}
                    },
                    "additionalProperties": False
                }
            }
        }
    ]

    sys_prompt = (
        "You are a Latest News Agent. First, ensure the following preferences are collected: "
        "tone, format, language, interaction, topics. Ask one question at a time until all are collected. "
        "When the user supplies a preference, call save_preferences with the structured values. "
        "After preferences are set, if the user requests news or summaries, use exa_news_fetch followed by summarize_news. "
        "Always return answers in the user's preferred language, tone, interaction style, and format."
    )

    # Build messages for OpenAI chat.completions
    oai_messages = [{"role": "system", "content": sys_prompt}]
    for m in messages:
        oai_messages.append({"role": m["role"], "content": m["content"]})
    # Inject preferences as JSON note
    oai_messages.append({"role": "system", "content": f"Current preferences JSON: {json.dumps(preferences)}"})

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # mutable prefs during loop
    prefs = dict(preferences)

    while True:
        payload = {
            "model": "gpt-4o",
            "messages": oai_messages,
            "tools": tools,
            "tool_choice": "auto",
        }
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=60)
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = {"error": resp.text}
            return {
                "assistant_message": f"OpenAI error {resp.status_code}: {detail}",
                "preferences": prefs,
            }
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls")

        if tool_calls:
            for tc in tool_calls:
                fname = tc["function"]["name"]
                fargs = json.loads(tc["function"].get("arguments", "{}"))

                if fname == "exa_news_fetch":
                    result = exa_news_fetch(**fargs)
                elif fname == "summarize_news":
                    # Merge defaults from prefs
                    fargs.setdefault("style", prefs.get("interaction", "concise"))
                    fargs.setdefault("format_", prefs.get("format", "bullet points"))
                    fargs.setdefault("language", prefs.get("language", "English"))
                    fargs.setdefault("tone", prefs.get("tone", "neutral"))
                    result = summarize_news(**fargs)
                elif fname == "save_preferences":
                    # Apply updates
                    for k in ["tone", "format", "language", "interaction", "topics"]:
                        if k in fargs and fargs[k] is not None:
                            if k == "topics" and isinstance(fargs[k], str):
                                prefs[k] = [s.strip() for s in fargs[k].split(",") if s.strip()]
                            else:
                                prefs[k] = fargs[k]
                    result = {"ok": True, "preferences": prefs}
                else:
                    result = {"error": f"Unknown tool {fname}"}

                # Append tool result
                oai_messages.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tc.get("id", "")
                })

            # Let the model see a system message with the latest prefs
            oai_messages.append({"role": "system", "content": f"Updated preferences JSON: {json.dumps(prefs)}"})
            continue
        else:
            # Normal assistant message
            assistant_content = message.get("content", "")
            return {
                "assistant_message": assistant_content,
                "preferences": prefs,
            }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if req.preferences is None:
        req.preferences = {}

    # Check which preferences are missing; ask questions if needed
    required = ["tone", "format", "language", "interaction", "topics"]
    updated = {**req.preferences}

    # If OpenAI is configured, let tool-calling handle dialog; otherwise simple logic
    result = openai_chat_with_tools([m.model_dump() for m in req.messages], updated)
    assistant_msg = result["assistant_message"]
    updated = result.get("preferences", updated)

    # Update preferences heuristically based on last user message in absence of NLP parsing
    # In a production app, you'd extract structured prefs via model. Here we rely on front-end form.

    messages_out = req.messages + [Message(role="assistant", content=assistant_msg)]

    return ChatResponse(messages=messages_out, updatedPreferences=updated)


@app.get("/health")
async def health():
    return {"status": "ok"}
