from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class EchoRequest(BaseModel):
    text: str

class EchoResponse(BaseModel):
    echo: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to the meta-dev API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/echo", response_model=EchoResponse)
async def echo(request: EchoRequest):
    return EchoResponse(echo=request.text)
