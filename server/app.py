from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage

import json
import subprocess
import os
import asyncio
import logging

from model import app_graph, llm as model
from pydantic import BaseModel


model_name = os.getenv("MODEL_NAME", "MrSplatchy/Cookama")  # You can change the model here to any ollama model you want in the .env file


def install_model(model_name: str):
    print(f"Installing model {model_name}...")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True, timeout=600)

    except subprocess.CalledProcessError:
        print(
            f"\nModel {model_name} cannot be downloaded, \nPlease check your internet connection"
        )
        raise SystemExit(1)

    except subprocess.TimeoutExpired:
        print(
            f"\nModel {model_name} is TAKING TOO LONG to download, \nStoping  Backend"
        )  # No this isn't a Deltarune referencee
        raise SystemExit(1)

    return print(f"Model {model_name} ready to use")


@asynccontextmanager
async def lifespan(app: FastAPI):
    install_model(model_name)
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    thread_id: int


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/")
async def chat(request: ChatRequest, stream: bool = Query(False)):

    if stream:
        # -------- STREAMING SSE --------
        async def event_generator():
            try:
                async for chunk in model.astream(request.message):
                    if chunk.content:
                        yield f"data: {json.dumps({'token': chunk.content})}\n\n"
                yield "data: [DONE]\n\n"
            except asyncio.CancelledError:
                # Client disconnected; silently exit
                return
            except Exception as e:
                logging.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"
                return

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    
    elif not stream:
        # -------- NON-STREAMING --------
        try:
            result = app_graph.invoke(
                {"messages": [HumanMessage(content=request.message)]},
                config={"configurable": {"thread_id": request.thread_id}},
            )
            return JSONResponse({"reply": result["messages"][-1].content})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)