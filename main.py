from fastapi import FastAPI

app = FastAPI()

@app.get("/", response_model=dict)
async def root():
    return {"message": "Welcome to the meta-dev API!"}

@app.get("/health", response_model=dict)
async def health():
    return {"status": "healthy"}