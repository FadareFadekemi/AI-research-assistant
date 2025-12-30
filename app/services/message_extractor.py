from app.core.llm import get_llm
import json
import re
from typing import Optional


def _heuristic_extract(text: str) -> Optional[dict]:
    # quoted pairs
    quotes = re.findall(r'["']([^"']+)["']', text)
    if len(quotes) >= 2:
        return {"x": quotes[0].strip(), "y": quotes[1].strip(), "method": "heuristic:quoted", "confidence": 0.9}

    # X vs Y or X versus Y
    m = re.search(r"(.+?)\s+(?:vs\.?|versus| v | v\.)\s+(.+)", text, flags=re.I)
    if m:
        left = m.group(1).strip().strip(':;,')
        right = m.group(2).strip().strip(':;,')
        return {"x": left, "y": right, "method": "heuristic:vs", "confidence": 0.75}

    # other heuristics: 'A against B', 'A by B', 'A versus B'
    m = re.search(r"(.+?)\s+(?:against|by)\s+(.+)", text, flags=re.I)
    if m:
        left = m.group(1).strip().strip(':;,')
        right = m.group(2).strip().strip(':;,')
        return {"x": left, "y": right, "method": "heuristic:against/by", "confidence": 0.7}

    return None


def _parse_llm_response(resp_text: str) -> Optional[dict]:
    # Try JSON
    try:
        data = json.loads(resp_text)
        x = data.get("x") or data.get("left") or data.get("a")
        y = data.get("y") or data.get("right") or data.get("b")
        confidence = data.get("confidence") or data.get("score") or None
        if x and y:
            return {"x": x.strip(), "y": y.strip(), "method": "llm", "confidence": float(confidence) if confidence else None}
    except Exception:
        pass

    # Try simple key-value lines like "x: col_a\ny: col_b"
    m_x = re.search(r"x\s*[:=]\s*([^\n,]+)", resp_text, flags=re.I)
    m_y = re.search(r"y\s*[:=]\s*([^\n,]+)", resp_text, flags=re.I)
    if m_x and m_y:
        return {"x": m_x.group(1).strip(), "y": m_y.group(1).strip(), "method": "llm", "confidence": None}

    return None


def extract_xy(message: str, llm_callable: Optional[callable] = None, timeout_seconds: int = 5) -> Optional[dict]:
    """Try to extract an (x, y) pair from the user's message.

    Strategy:
    1) If an LLM callable is available (passed in or via get_llm), use it to extract a JSON-like response.
    2) If LLM fails or is not available, use local heuristics.

    Returns: {"x":..., "y":..., "method": ..., "confidence": float} or None
    """
    msg = (message or "").strip()

    # 1) Try heuristic quick match first (cheap and often sufficient)
    heuristic = _heuristic_extract(msg)

    # 2) Attempt LLM extraction if callable provided or if we can obtain an LLM
    llm = None
    if llm_callable is not None:
        llm = llm_callable
    else:
        try:
            llm = get_llm()
        except Exception:
            llm = None

    if llm:
        prompt = (
            "You are an assistant that extracts two column references (X and Y) a user wants to compare or plot from a short natural-language message.\n"
            "Return STRICT JSON only with keys 'x' and 'y' and optional 'confidence'. Examples follow (do not include explanations):\n"
            "1) 'Plot "Which feature...?" vs "How long...?"' -> {\"x\": \"Which feature...?\", \"y\": \"How long...?\"}\n"
            "2) 'Compare income tracking against business size' -> {\"x\": \"How do you currently track your business income and expenses?\", \"y\": \"How many people (including you) work in your business?\"}\n"
            "3) 'Show me a count of payment method by team size' -> {\"x\": \"payment method\", \"y\": \"team size\"}\n"
            "If you cannot be confident, return your best guess with a 'confidence' float (0..1). If nothing relevant, return an empty JSON {}.\n"
            f"User message: \"{msg}\"\n"
        )
        try:
            # LLMs may be callable or have a generate method; accept both
            raw = None
            try:
                raw = llm(prompt)
            except Exception:
                if hasattr(llm, "generate"):
                    raw_resp = llm.generate(prompt)
                    raw = getattr(raw_resp, "text", None) or getattr(raw_resp, "content", None) or str(raw_resp)

            if raw:
                # raw may be object; coerce to str
                raw_text = raw if isinstance(raw, str) else str(raw)
                parsed = _parse_llm_response(raw_text)
                if parsed:
                    return parsed
        except Exception:
            # fall through to heuristic if LLM fails
            pass

    # Return heuristic result (even if None)
    return heuristic
