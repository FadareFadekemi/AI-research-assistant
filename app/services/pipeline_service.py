import json
import logging
from crewai import Task
from app.agents.orchestrator import orchestrator_agent
from app.services.analysis_service import run_analysis
from app.services.literature_service import run_literature_review
from app.services.discussion_service import run_discussion_service
from app.services.chat_service import run_chat_service  

logger = logging.getLogger(__name__)

async def run_pipeline(
    user_message: str | None = None,
    dataset=None,
    mode: str | None = None,
    word_count: int = 500,
    tone: str = "formal",
    **kwargs 
):
    """
    Conversational research pipeline orchestrator.
    Coordinates between Chat, Literature Review, Data Analysis, and Narrative Discussion.
    """

    plan = None

    # --- Step 1: Orchestration & Planning ---
    if user_message:
        # The Orchestrator now decides if the intent is "chat" or "research"
        task = Task(
            description=f"""
You are AIRA, a research orchestrator. Analyze the user request and generate a structured research plan.

User message:
{user_message}

CRITICAL INSTRUCTIONS:
1. If the user is GREETING you or asking GENERAL non-research questions, set "mode": "chat".
2. If the user asks to plot/chart/visualize ONE variable (e.g., "Plot Gender"), ONLY include that tool with one variable.
3. NEVER add a 'hue' unless the user explicitly uses comparison keywords like 'by', 'vs', 'relationship'.
4. Do NOT invent column names.
5. System context: A dataset HAS already been provided. Do NOT ask for it.

Return STRICT JSON:
{{
  "needs_clarification": boolean,
  "clarification_question": string | null,
  "mode": "chat" | "literature" | "analysis" | "discussion" | "full",
  "literature_plan": {{
    "focus": string | null,
    "tone": string | null,
    "word_count": number | null
  }},
  "analysis_plan": [
    {{
      "tool": string,
      "reason": string,
      "interpret": boolean | null
    }}
  ],
  "discussion_plan": {{
    "focus": string | null
  }}
}}
""",
            expected_output="Valid JSON object representing the research plan.",
        )

        plan_raw = orchestrator_agent.execute_task(task)
        
        # Robust JSON cleaning
        if "```json" in plan_raw:
            plan_raw = plan_raw.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_raw:
            plan_raw = plan_raw.split("```")[1].split("```")[0].strip()
            
        try:
            plan = json.loads(plan_raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse orchestrator plan. Defaulting to chat.")
            plan = {"mode": "chat"}

        # --- NEW: Step 1.5: Chat Branching ---
        if plan.get("mode") == "chat":
            chat_content = await run_chat_service(user_message)
            return {
                "type": "text",
                "content": chat_content,
                "visuals": {},
                "exports": {}
            }

        if plan.get("needs_clarification"):
            return {
                "type": "clarification",
                "content": plan.get("clarification_question"),
            }

        # Update parameters based on Orchestrator's plan
        mode = plan.get("mode") or mode
        tone = plan.get("literature_plan", {}).get("tone") or tone
        word_count = plan.get("literature_plan", {}).get("word_count") or word_count

    literature = None
    analysis = None
    discussion_block = None

    # --- Step 2: Literature Stage ---
    if mode in {"literature", "full"}:
        literature = await run_literature_review(
            topic=plan.get("literature_plan", {}).get("focus"),
            word_count=word_count,
            tone=tone,
        )

    # --- Step 3: Analysis Stage ---
    if mode in {"analysis", "full"}:
        if not dataset:
            return {
                "type": "text",
                "content": "I am ready to help, but I need a dataset to perform analysis. Please upload one in the sidebar."
            }

        analysis = await run_analysis(
            dataset=dataset,
            analysis_plan=plan.get("analysis_plan", []),
            user_message=user_message,
        )

    # --- Step 4: Discussion Stage ---
    if mode in {"discussion", "full"}:
        topic_focus = plan.get("discussion_plan", {}).get("focus") or plan.get("literature_plan", {}).get("focus")
        
        findings_context = None
        if analysis and isinstance(analysis, dict):
            findings_context = analysis.get("content")
        
        if not findings_context:
            findings_context = user_message

        discussion_res = await run_discussion_service(
            topic=topic_focus,
            findings=findings_context,
            word_count=word_count
        )
        
        body = discussion_res.get("discussion_body", "No discussion generated.")
        refs = "\n".join(discussion_res.get("references", []))
        impl = "\n- ".join(discussion_res.get("implications", []))
        lims = "\n- ".join(discussion_res.get("limitations", []))
        recs = "\n- ".join(discussion_res.get("recommendations", []))
        
        discussion_block = (
            f"{body}\n\n"
            f"### Implications\n{impl}\n\n"
            f"### Limitations\n{lims}\n\n"
            f"### Recommendations\n{recs}\n\n"
            f"### References\n{refs}"
        )

    # --- Step 5: Response Normalization & Return ---
    visuals = analysis.get("visuals") if isinstance(analysis, dict) else {}
    exports = analysis.get("exports") if isinstance(analysis, dict) else {}

    if mode == "literature":
        return {
            "type": "text",
            "content": literature.get("literature_review", literature),
        }

    if mode == "discussion":
        return {
            "type": "text",
            "content": discussion_block,
        }

    if mode == "analysis":
        return {
            "type": "analysis",
            "content": analysis.get("content") if isinstance(analysis, dict) else str(analysis),
            "visuals": visuals,
            "exports": exports,
        }

    # Full pipeline
    full_text = []
    if literature: full_text.append(f"## Literature Review\n{literature.get('literature_review', '')}")
    if analysis: full_text.append(f"## Analysis Interpretation\n{analysis.get('content', '')}")
    if discussion_block: full_text.append(f"## Discussion & Conclusion\n{discussion_block}")

    return {
        "type": "full",
        "content": "\n\n---\n\n".join(full_text),
        "visuals": visuals,
        "exports": exports,
        "literature": literature,
        "analysis": analysis,
        "discussion": discussion_block, 
    }