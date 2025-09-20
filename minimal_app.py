from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Minimal App - Health Check Only"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
