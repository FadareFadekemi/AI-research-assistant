from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.pipeline_service import run_pipeline

router = APIRouter(prefix="/research", tags=["Research"])

ALLOWED_EXTENSIONS = {"csv", "xlsx"}


@router.post("/run")
async def run_research(
    message: str = Form(
        ...,
        description="User's research request in natural language"
    ),
    dataset: UploadFile | None = File(
        None,
        description="Optional dataset (required for analysis)"
    ),
    debug: bool = Form(False, description="Log orchestrator plan and step execution"),
    show_agent_reasoning: bool = Form(False, description="Run analysis steps via the agent to expose reasoning (slower)")
):
    """
    Conversational research endpoint.
    The system infers intent (literature / analysis / discussion / full)
    from the user's message.
    """

    # -------------------------
    # Validate dataset if provided
    # -------------------------
    if dataset:
        if not dataset.filename:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file has no filename"
            )

        ext = dataset.filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Only CSV and XLSX files are supported"
            )

    # -------------------------
    # Run conversational pipeline
    # -------------------------
    try:
        result = await run_pipeline(
            user_message=message,
            dataset=dataset,
            debug=debug,
            show_agent_reasoning=show_agent_reasoning
        )
        return result
    except Exception as e:
        # Log with traceback so server logs show the error
        import logging, traceback
        logging.getLogger(__name__).exception("Pipeline failed: %s", e)
        # Return a helpful HTTP 500 with the error message
        raise HTTPException(status_code=500, detail=f"Pipeline run failed: {str(e)}")
