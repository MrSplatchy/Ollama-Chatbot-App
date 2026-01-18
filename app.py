from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from model import generateResponse, model, url
import requests

@asynccontextmanager
async def installModel(_:FastAPI):
    requests.post(
        f"{url}/api/pull",
        json={"name": model},
        timeout=300
    )
    yield
    
app = FastAPI(lifespan=installModel)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

conversation_history= []


@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def ask(request: Request, prompt: str = Form(...)):
    global conversation_history
    conversation_history = conversation_history[-8:]

    conversation_history.append({"role": "user", "content": prompt})

    try:
        return StreamingResponse(generateResponse(prompt, conversation_history), media_type="text/plain")
    
    except Exception as e:
        return StreamingResponse(iter([f"Error: {str(e)}"]), media_type="text/plain")


@app.get("/health")
async def health_check():
    while True:
        return {"status": "ok"}

