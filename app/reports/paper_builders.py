from app.models.research import FullPipelineResponse

def build_paper_sections(result: FullPipelineResponse) -> dict:
    return {
        "abstract": result.literature.theme_summary,
        "introduction": "\n".join(result.literature.key_findings),
        "methods": "Data were analyzed using descriptive and inferential statistics.",
        "results": str(result.analysis.descriptives),
        "discussion": result.discussion.discussion,
        "limitations": "\n".join(result.discussion.limitations),
        "references": "\n".join(result.discussion.references)
    }
