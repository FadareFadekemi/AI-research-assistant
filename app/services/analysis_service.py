import logging
from app.services.file_service import save_and_load_dataset

from app.tools.analysis_tools import descriptive_statistics
from app.tools.statistics_tools import chi_square_test, cronbach_alpha
from app.tools.visualization_tools import countplot, barplot, piechart

from app.agents.analysis import analysis_agent
from app.utils.column_matcher import (
    extract_candidate_phrases,
    resolve_column,
)

logger = logging.getLogger(__name__)


TOOL_REGISTRY = {
    "descriptive_statistics": descriptive_statistics,
    "chi_square_test": chi_square_test,
    "cronbach_alpha": cronbach_alpha,
    "countplot": countplot,
    "barplot": barplot,
    "piechart": piechart,
}

VISUALIZATION_TOOLS = {"countplot", "barplot", "piechart"}


def interpret_with_llm(text: str) -> str:
    """
    Safe interpretation using CrewAI/OpenAICompletion LLM.
    """
    llm = analysis_agent.llm
    
    prompt = f"""
Interpret the following statistical output in clear, simple language.
Avoid technical jargon and explain what it means practically.

{text}
"""

    
    try:
        response = llm.call(prompt)
    except AttributeError:
        
        response = llm.predict(prompt)

    if isinstance(response, str):
        return response

    return getattr(response, "content", str(response))
    
async def run_analysis(
    dataset,
    analysis_plan: list[dict] | None = None,
    user_message: str | None = None,
    debug: bool = False,
    **kwargs,  
):
    path, df = await save_and_load_dataset(dataset)
    results = {}

    if not analysis_plan:
        return results

    for step in analysis_plan:
        tool_name = step.get("tool")
        interpret = step.get("interpret", False)

        if tool_name not in TOOL_REGISTRY:
            results[tool_name] = f"Unknown tool: {tool_name}"
            continue

        tool = TOOL_REGISTRY[tool_name]

        try:
            
            if tool_name == "descriptive_statistics":
                output = tool.run(path)

                if interpret:
                    results[tool_name] = {
                        "result": output,
                        "interpretation": interpret_with_llm(output),
                    }
                else:
                    results[tool_name] = output

            
            elif tool_name in VISUALIZATION_TOOLS:
                if not user_message:
                    raise ValueError(f"{tool_name} requires user_message")

                
                phrase_1, phrase_2 = extract_candidate_phrases(user_message)

                phrases = [p for p in [phrase_1, phrase_2] if p]

                
                if not phrases:
                    phrases = [user_message]

                
                resolved_columns = []
                for phrase in phrases:
                    col = await resolve_column(phrase, list(df.columns))
                    if col and col not in resolved_columns:
                        resolved_columns.append(col)

                if not resolved_columns:
                    raise ValueError(f"Could not resolve columns for {tool_name}")

                x_col = resolved_columns[0]
                hue_col = resolved_columns[1] if len(resolved_columns) > 1 else None

                records = df.to_dict(orient="records")

                
                if tool_name in {"countplot", "barplot"}:
                    output = tool.run(records, x=x_col, hue=hue_col)

                elif tool_name == "piechart":
                    output = tool.run(records, column=x_col)

                results[tool_name] = output

            
            elif tool_name == "chi_square_test":
                if not user_message:
                    raise ValueError("Chi-square requires user_message")

                phrase_1, phrase_2 = extract_candidate_phrases(user_message)

                if not phrase_1 or not phrase_2:
                    raise ValueError("Chi-square requires two variables")

                col1 = await resolve_column(phrase_1, list(df.columns))
                col2 = await resolve_column(phrase_2, list(df.columns))

                if not col1 or not col2:
                    raise ValueError("Could not resolve outcome or predictor columns")

                output = tool.run(
                    df.to_dict(orient="records"),
                    outcome=col1,
                    predictors=[col2],
                )

                if interpret:
                    results[tool_name] = {
                        "result": output,
                        "interpretation": interpret_with_llm(output),
                    }
                else:
                    results[tool_name] = output

            
            elif tool_name == "cronbach_alpha":
                output = tool.run(df.to_dict(orient="records"))

                if interpret:
                    results[tool_name] = {
                        "result": output,
                        "interpretation": interpret_with_llm(output),
                    }
                else:
                    results[tool_name] = output

        except Exception as e:
            logger.exception(e)
            results[tool_name] = f"Error executing {tool_name}: {str(e)}"

    return results
