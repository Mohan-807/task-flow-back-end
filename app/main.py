from fastapi import FastAPI

app = FastAPI(
    title="TaskFlow Backend API",
    description="Backend API for TaskFlow",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}