import json
from crewai import Task
from app.agents.orchestrator import orchestrator_agent
from app.services.analysis_service import run_analysis
from app.services.literature_service import run_literature_review
from app.services.discussion_service import run_discussion


async def run_pipeline(
    user_message: str | None = None,
    dataset=None,
    mode: str | None = None,
    word_count: int = 500,
    tone: str = "formal",
    **kwargs
):
    """
    Conversational research pipeline.
    Orchestrator decides mode, analysis plan, and flow.
    """
    plan = None

    # ------------------------
    # STEP 1: Orchestrator generates plan
    # ------------------------
    if user_message:
        task = Task(
            description=f"""
You are a research orchestrator.

User message:
{user_message}
System context:
- A dataset HAS already been provided to the system.
- Do NOT ask which dataset to use.
- Only ask for clarification if the analysis intent or comparison is unclear.

Return STRICT JSON:
{{
  "needs_clarification": boolean,
  "clarification_question": string | null,
  "mode": "literature" | "analysis" | "discussion" | "full",
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
            expected_output="Valid JSON only",
        )

        plan_raw = orchestrator_agent.execute_task(task)
        plan = json.loads(plan_raw)

        if plan.get("needs_clarification"):
            return {
                "status": "needs_clarification",
                "question": plan.get("clarification_question"),
            }

        mode = plan.get("mode") or mode
        tone = plan.get("literature_plan", {}).get("tone") or tone
        word_count = plan.get("literature_plan", {}).get("word_count") or word_count

    # ------------------------
    # STEP 2: Execute pipeline
    # ------------------------
    result = {}

    # Literature
    if mode in {"literature", "full"}:
        result["literature"] = await run_literature_review(
            topic=plan.get("literature_plan", {}).get("focus"),
            word_count=word_count,
            tone=tone,
        )

    # Analysis
    if mode in {"analysis", "full"}:
        if not dataset:
            raise ValueError("Dataset required for analysis")

        result["analysis"] = await run_analysis(
            dataset=dataset,
            analysis_plan=plan.get("analysis_plan", []),
            user_message=user_message,
        )

    # Discussion
    if mode in {"discussion", "full"}:
        result["discussion"] = await run_discussion(
            analysis=result.get("analysis"),
            literature=result.get("literature"),
            plan=plan.get("discussion_plan"),
        )

    return result
