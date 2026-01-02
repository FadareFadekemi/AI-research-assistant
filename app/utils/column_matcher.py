import re
import json
import logging
from typing import List, Optional, Tuple
from app.core.llm import get_llm

logger = logging.getLogger(__name__)
llm = get_llm()

# Confidence threshold for matching
CONFIDENCE_THRESHOLD = 0.65

def aggressive_clean(text: str) -> str:
    """Removes standard spaces, non-breaking spaces (\xa0), and newlines."""
    if not text:
        return ""
    # Remove \xa0 and other whitespace characters
    text = re.sub(r'\s+', ' ', text) 
    return text.strip()

async def resolve_column(
    phrase: str, 
    columns: List[str], 
    threshold: float = CONFIDENCE_THRESHOLD
) -> Optional[str]:
    if not phrase:
        return None

    phrase_clean = aggressive_clean(phrase).lower()
    
    # 1. Direct match with aggressive cleaning on both sides
    for col in columns:
        if phrase_clean == aggressive_clean(col).lower():
            return col

    # ... rest of your LLM semantic match code ...

async def extract_candidate_phrases(user_message: str, columns: List[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Uses LLM to identify variables in the user's request.
    Now accepts the column list to ensure it extracts phrases that actually exist.
    """
    column_context = f"\nAvailable Columns: {columns}" if columns else ""
    
    prompt = f"""
    Analyze this research request: "{user_message}"
    {column_context}
    
    Task: Identify the specific variables or data columns the user wants to analyze.
    
    Rules:
    1. If the user wants to see ONE variable, set phrase_1 to the variable and phrase_2 to null.
    2. If comparing/relating TWO variables, set phrase_1 and phrase_2.
    3. Use the exact wording from the column list if provided.
    4. Remove action verbs like "plot", "show", "calculate".
    
    Return ONLY a JSON object:
    {{"phrase_1": "string", "phrase_2": "string or null"}}
    """
    
    try:
        response = await llm.ainvoke(prompt)
        content = response.content
        
        # Clean JSON markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        parsed = json.loads(content)
        return parsed.get("phrase_1"), parsed.get("phrase_2")
    except Exception as e:
        logger.error(f"LLM Phrase Extraction failed: {e}")
        return user_message, None

async def resolve_column(
    phrase: str, 
    columns: List[str], 
    threshold: float = CONFIDENCE_THRESHOLD
) -> Optional[str]:
    """
    Matches a natural language phrase to the most likely dataset column.
    """
    if not phrase:
        return None

    # 1. Direct match (case-insensitive)
    phrase_clean = phrase.strip().lower()
    for col in columns:
        if phrase_clean == col.strip().lower():
            return col

    # 2. Semantic Match
    prompt = f"""
    Target Concept: "{phrase}"
    Available Columns: {columns}
    
    Which column from the list BEST matches the target concept? 
    If no column is a clear match, return null.
    
    Return ONLY a JSON object:
    {{"best_column": "string or null", "confidence": float}}
    """
    
    try:
        response = await llm.ainvoke(prompt)
        content = response.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        parsed = json.loads(content)
        best_col = parsed.get("best_column")
        confidence = parsed.get("confidence", 0.0)
        
        if best_col in columns and confidence >= threshold:
            return best_col
    except Exception as e:
        logger.error(f"Semantic Column Match failed: {e}")
    
    return None