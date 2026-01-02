from fastapi import FastAPI
from app.api.research import router as research_router
from app.api.download import router as download_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AIRA - AI Research Assistant",
    description="Backend API for conversational data analysis, statistics, and research workflows",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/")
async def root():
    return {"status": "ok", "message": "AIRA is running smoothly 🚀"}

@app.get("/health")
async def health_check():
    return {"service": "AIRA", "status": "healthy"}


app.include_router(research_router)
app.include_router(download_router)
