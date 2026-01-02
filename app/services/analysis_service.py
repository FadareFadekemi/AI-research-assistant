import logging
import os
import re
import pandas as pd
from uuid import uuid4
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
EXPORT_DIR = "outputs/exports"
PLOT_DIR = "outputs/plots"
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

def heavy_clean_column(col_name):
    """
    Removes newlines, tabs, and non-breaking spaces (\xa0) 
    that often appear in survey exports.
    """
    if not col_name:
        return col_name
    # Replace all whitespace sequences (including \xa0) with a single space
    cleaned = re.sub(r'\s+', ' ', str(col_name))
    return cleaned.strip()

def interpret_with_llm(text: str) -> str:
    """Uses the LLM to provide a narrative explanation of statistical data."""
    llm = analysis_agent.llm
    prompt = f"Interpret the following statistical output in simple language:\n\n{text}"
    try:
        response = llm.call(prompt)
    except Exception as e:
        logger.error(f"LLM Interpretation failed: {e}")
        return "Statistical output generated, but interpretation failed."
    
    return getattr(response, "content", str(response))

def export_results_to_excel(results: dict) -> str:
    """Saves analysis results to an Excel file."""
    file_path = os.path.join(EXPORT_DIR, f"analysis_results_{uuid4().hex}.xlsx")
    sheets_written = 0

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        for tool, content in results.items():
            if isinstance(content, dict) and "file" in content and "result" not in content:
                continue
            data = content["result"] if isinstance(content, dict) and "result" in content else content
            try:
                df_out = pd.DataFrame(data) if isinstance(data, (list, dict)) and len(data) > 0 else pd.DataFrame({"Output": [str(data)]})
                df_out.to_excel(writer, sheet_name=tool[:31], index=False)
                sheets_written += 1
            except Exception as e:
                logger.warning(f"Skipping Excel sheet for {tool}: {e}")
        if sheets_written == 0:
            pd.DataFrame({"Message": ["No tabular data generated."]}).to_excel(writer, sheet_name="Summary")
    return file_path

async def run_analysis(dataset, analysis_plan=None, user_message=None, **kwargs):
    path, df = await save_and_load_dataset(dataset)
    
    # --- STEP 1: HEAVY CLEAN HEADERS ---
    # Aligns DataFrame columns with LLM extracted phrases
    df.columns = [heavy_clean_column(col) for col in df.columns]
    available_cols = list(df.columns)
    logger.info(f"AIRA Cleaned Headers: {available_cols}")

    results = {}
    export_plots = []
    interpretations = []

    if not analysis_plan:
        return {"content": "No analysis plan provided.", "exports": {}}

    for step in analysis_plan:
        tool_name = step.get("tool")
        interpret = step.get("interpret", False)
        if tool_name not in TOOL_REGISTRY: continue
        tool = TOOL_REGISTRY[tool_name]

        try:
            # --- 1. DESCRIPTIVE STATISTICS ---
            if tool_name == "descriptive_statistics":
                output = tool.run(path)
                if interpret:
                    text = interpret_with_llm(output)
                    interpretations.append(f"### Descriptive Analysis\n{text}")
                    results[tool_name] = {"result": output, "interpretation": text}
                else:
                    results[tool_name] = output

            # --- 2. VISUALIZATIONS ---
            elif tool_name in VISUALIZATION_TOOLS:
                p1, p2 = await extract_candidate_phrases(user_message, available_cols)
                col1 = await resolve_column(p1, available_cols)
                col2 = await resolve_column(p2, available_cols) if p2 else None
                
                if not col1:
                    col1 = await resolve_column(user_message, available_cols)

                if not col1:
                    raise ValueError(f"Could not resolve columns for {tool_name}")
                
                # CACHE BUSTING: Generate a unique filename for every plot
                unique_filename = os.path.join(PLOT_DIR, f"{tool_name}_{uuid4().hex[:8]}.png")
                
                records = df.to_dict(orient="records")
                if tool_name in {"countplot", "barplot"}:
                    logger.info(f"Plotting {tool_name}: x='{col1}', hue='{col2}'")
                    output = tool.run(records, x=col1, hue=col2, filename=unique_filename)
                else:
                    output = tool.run(records, column=col1, filename=unique_filename)
                
                results[tool_name] = output
                if isinstance(output, dict) and "file" in output: 
                    export_plots.append(output["file"])

            # --- 3. CHI-SQUARE TESTS ---
            elif tool_name == "chi_square_test":
                p1, p2 = await extract_candidate_phrases(user_message, available_cols)
                c1 = await resolve_column(p1, available_cols)
                c2 = await resolve_column(p2, available_cols)
                
                if not c1 or not c2:
                    prompt = (
                        f"Identify TWO categorical columns from: {available_cols} "
                        f"based on the request: '{user_message}'. "
                        "Return ONLY the column names separated by a comma."
                    )
                    raw_res = analysis_agent.llm.call(prompt)
                    res_text = getattr(raw_res, "content", str(raw_res)).strip()
                    
                    cols = [heavy_clean_column(x) for x in res_text.split(",")]
                    c1 = cols[0] if len(cols) > 0 else c1
                    c2 = cols[1] if len(cols) > 1 else c2

                if not c1 or not c2: 
                    raise ValueError(f"Chi-square needs 2 variables. Resolved: {c1} and {c2}")
                
                output = tool.run(df.to_dict(orient="records"), outcome=c1, predictors=[c2])
                if interpret:
                    text = interpret_with_llm(output)
                    interpretations.append(f"### Chi-Square Analysis ({c1} vs {c2})\n{text}")
                    results[tool_name] = {"result": output, "interpretation": text}
                else: 
                    results[tool_name] = output

            # --- 4. CRONBACH ALPHA ---
            elif tool_name == "cronbach_alpha":
                output = tool.run(df.to_dict(orient="records"))
                if interpret:
                    text = interpret_with_llm(output)
                    interpretations.append(f"### Reliability Analysis\n{text}")
                    results[tool_name] = {"result": output, "interpretation": text}
                else:
                    results[tool_name] = output

        except Exception as e:
            logger.error(f"Error in {tool_name}: {e}")
            results[tool_name] = f"Error: {str(e)}"

    return {
        "content": "\n\n".join(interpretations) if interpretations else "Analysis complete.",
        "visuals": {f"Chart {i+1}": path for i, path in enumerate(export_plots)},
        "exports": {
            "excel": export_results_to_excel(results),
            "plots": export_plots,
        },
    }