"""
PaisaSense AI — AI Engine
Handles Gemini and OpenRouter API calls, prompt building, and fallback responses.
"""

import os
import requests


GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL       = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"


# ── API Callers ────────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> str | None:
    if not GEMINI_API_KEY:
        return None
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 250, "temperature": 0.7},
    }
    try:
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload, timeout=20,
        )
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


def call_openrouter(prompt: str) -> str | None:
    if not OPENROUTER_API_KEY:
        print("❌ OpenRouter API key missing")
        return None
    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model":       "openai/gpt-3.5-turbo",
                "messages":    [{"role": "user", "content": prompt}],
                "max_tokens":  250,
                "temperature": 0.7,
            },
            timeout=20,
        )
        print("🤖 OpenRouter RAW RESPONSE:", response.text)
        data = response.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        print("❌ OpenRouter unexpected response:", data)
        return None
    except Exception as e:
        print("❌ OpenRouter ERROR:", str(e))
        return None


def get_ai_response(prompt: str) -> tuple[str | None, str]:
    """
    Try Gemini first, fall back to OpenRouter.
    Returns (text, source) where source is 'gemini', 'openrouter', or 'fallback'.
    """
    text = call_gemini(prompt)
    if text:
        return text, "gemini"

    text = call_openrouter(prompt)
    if text:
        return text, "openrouter"

    return None, "fallback"


# ── Prompt Builders ────────────────────────────────────────────────────────────

def _lang_instruction(language: str) -> str:
    if language == "hi":
        return "केवल हिंदी में उत्तर दें। अंग्रेजी का उपयोग न करें।"
    elif language == "hi-en":
        return "Respond in Hinglish (Hindi + English mix, casual tone). Mix both languages naturally."
    return "Respond in plain English."


def build_analysis_prompt(insights: dict, language: str = "en") -> str:
    s = insights.get("summary", {})
    b = insights.get("behavior", {})
    c = insights.get("category_totals", {})
    return f"""You are a sharp Indian fintech advisor. Be practical, not generic. {_lang_instruction(language)}

Spending data:
- Total: ₹{s.get('total_spent')} | Avg daily: ₹{s.get('avg_daily_spend')}
- Top category: {s.get('top_category')} | Weekend: {b.get('weekend_pct')}% of spend
- Categories: {c}

Give exactly:
1. One key insight
2. One risk warning
3. One action step

Under 120 words. Be direct. No filler.
"""


def build_voice_prompt(user_query: str, context: dict, language: str = "en") -> str:
    summary  = context.get("summary", {})
    cats     = context.get("category_totals", {})
    behavior = context.get("behavior", {})
    subs     = context.get("subscriptions", {})
    savings  = context.get("savings", {})
    total    = summary.get("total_spent") or 1

    cat_lines = [
        f"  - {cat}: ₹{amt:,.0f} ({round(amt / total * 100)}%)"
        for cat, amt in cats.items()
    ]
    cat_breakdown = "\n".join(cat_lines) if cat_lines else "  - No category data"

    context_block = f"""User's actual spending data:
- Total spent: ₹{summary.get('total_spent', 0):,.0f} over {summary.get('date_range_days', 0)} days
- Daily average: ₹{summary.get('avg_daily_spend', 0):,.0f}/day
- Top category: {summary.get('top_category', 'N/A')}
- Category breakdown:
{cat_breakdown}
- Weekend spending: ₹{behavior.get('weekend_total', 0):,.0f} ({behavior.get('weekend_pct', 0)}% of total)
- Micro-transactions (<₹200): {behavior.get('small_txn_count', 0)} transactions, ₹{behavior.get('small_txn_total', 0):,.0f} total
- Subscriptions: ₹{subs.get('total', 0):,.0f}/month detected
- Potential monthly savings: ₹{savings.get('monthly', 0):,.0f}"""

    return f"""You are a personal financial advisor. {_lang_instruction(language)}

{context_block}

The user's specific question: "{user_query}"

IMPORTANT RULES:
- Answer THIS specific question directly — do not give a generic overview
- Use the actual ₹ numbers and % from the data above
- If the question is about a specific category (food, travel etc), focus only on that
- Keep answer under 80 words
- Give 1 clear, actionable suggestion at the end
- Do not start with "Great question" or filler phrases
"""


# ── Fallback Text Generators ───────────────────────────────────────────────────

def fallback_analysis(insights: dict, language: str = "en") -> str:
    s    = insights.get("summary", {})
    b    = insights.get("behavior", {})
    c    = insights.get("category_totals", {})
    top  = s.get("top_category", "Others")
    food = c.get("Food", 0)
    saving = round(food * 0.2, 0) if food else 0

    if language == "hi":
        text = (
            f"आपके खर्च का विश्लेषण दर्शाता है कि आपने कुल ₹{s.get('total_spent', 0):,.0f} खर्च किए, "
            f"जिसमें औसत दैनिक खर्च ₹{s.get('avg_daily_spend', 0):,.0f} रहा। "
            f"आपकी सबसे बड़ी खर्च श्रेणी {top} है — इस पर ध्यान देना जरूरी है। "
        )
        if b.get("weekend_pct", 0) > 30:
            text += f"आपके {b['weekend_pct']}% खर्च सप्ताहांत में होते हैं — एक सीमा तय करें। "
        if food > 0:
            text += f"खाने के खर्च को 20% कम करके आप ₹{saving:,.0f}/माह बचा सकते हैं। "
        text += "छोटी-छोटी बचत से बड़ा आर्थिक सुरक्षा कवच बनता है।"
    else:
        text = (
            f"Your spending analysis shows a total outflow of ₹{s.get('total_spent', 0):,.0f} "
            f"with an average daily spend of ₹{s.get('avg_daily_spend', 0):,.0f}. "
            f"Your biggest expense category is {top}, which is worth keeping a close eye on. "
        )
        if b.get("weekend_pct", 0) > 30:
            text += f"A notable {b['weekend_pct']}% of your money flows out on weekends — try setting a weekend spending cap. "
        if food > 0:
            text += f"Trimming food delivery by 20% alone could free up ₹{saving:,.0f} per month. "
        text += "Small consistent cuts across categories add up — even saving 10% monthly builds a strong financial cushion over time."

    return text


def fallback_voice(language: str = "en") -> str:
    if language == "en":
        return "I couldn't get a response right now. Please try again."
    return "अभी जवाब देने में समस्या है। कृपया दोबारा पूछें।"
