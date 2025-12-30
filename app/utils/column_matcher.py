import re
import json
from difflib import SequenceMatcher
from typing import List, Optional, Tuple
from app.core.llm import get_llm

CONFIDENCE_THRESHOLD = 0.65
llm = get_llm()



def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def extract_candidate_phrases(user_message: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts two possible column phrases from natural language.

    Supports:
    - compare X with Y
    - X and Y
    - X by Y
    - X vs Y
    - X across Y
    """
    patterns = [
        r"compare\s+(.*?)\s+(?:with|and)\s+(.*)",
        r"(.*?)\s+(?:with|and|by|vs|versus|across)\s+(.*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()

    return None, None


def resolve_column_from_phrase(
    phrase: str,
    dataset_columns: List[str]
) -> Tuple[Optional[str], float]:

    if not phrase:
        return None, 0.0

    phrase_norm = normalize(phrase)
    best_match, best_score = None, 0.0

    for col in dataset_columns:
        score = similarity(phrase_norm, normalize(col))
        if score > best_score:
            best_match, best_score = col, score

    return best_match, best_score



async def semantic_column_match(user_phrase: str, dataset_columns: List[str]):
    prompt = f"""
You are given dataset columns:

{dataset_columns}

User wants:
"{user_phrase}"

Return STRICT JSON only:
{{
  "best_column": string | null,
  "confidence": number between 0 and 1
}}

Rules:
- Choose only from provided columns
- Return null if uncertain
"""

    response = llm.invoke(prompt)

    try:
        parsed = json.loads(response.content)
        return parsed.get("best_column"), parsed.get("confidence", 0)
    except Exception:
        return None, 0


async def resolve_column(
    phrase: str,
    columns: List[str],
    threshold: float = CONFIDENCE_THRESHOLD
) -> Optional[str]:

    if not phrase:
        return None

    # 1️⃣ Lexical
    col, conf = resolve_column_from_phrase(phrase, columns)
    if col and conf >= threshold:
        return col

 
    sem_col, sem_conf = await semantic_column_match(phrase, columns)
    if sem_col and sem_conf >= threshold:
        return sem_col

    return None
