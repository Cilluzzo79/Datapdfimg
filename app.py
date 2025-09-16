from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "Railway Document Worker is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
