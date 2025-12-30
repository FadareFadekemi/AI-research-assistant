import json
import io
import asyncio
import sys
import pathlib

# Add project root to path so we can import app
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.services import pipeline_service

class DummyDataset:
    def __init__(self, filename: str, bytes_content: bytes):
        self.filename = filename
        self._content = bytes_content
        self.file = io.BytesIO(bytes_content)
    async def read(self):
        return self._content

plan = {
    "needs_clarification": False,
    "clarification_question": None,
    "mode": "analysis",
    "literature_plan": {"focus": "topic", "tone": "formal", "word_count": 500},
    "analysis_plan": [
        {
            "tool": "Python",
            "reason": "user asked to analyze with Python",
            "visualizations_requested": False,
            "column": None
        }
    ],
    "discussion_plan": {"focus": ""}
}

async def fake_execute_task(task):
    return json.dumps(plan)

pipeline_service.orchestrator_agent.execute_task = fake_execute_task

async def fake_run_analysis(dataset, analysis_plan=None):
    print("received analysis_plan:", analysis_plan)
    return {"descriptive_statistics": {}}

pipeline_service.run_analysis = fake_run_analysis

async def main():
    csv_bytes = b"a,b\n1,2\n3,4\n"
    dataset = DummyDataset("data.csv", csv_bytes)
    print("Calling run_pipeline...")
    result = await pipeline_service.run_pipeline(user_message="Analyze the dataset", dataset=dataset)
    print("pipeline result:", result)

if __name__ == '__main__':
    asyncio.run(main())
