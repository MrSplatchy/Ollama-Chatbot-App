from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import json

app = FastAPI()

# Configuration de Jinja2 et des fichiers statiques
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Variable globale pour stocker l'historique de la conversation
conversation_history = []

@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def ask(request: Request, prompt: str = Form(...)):
    global conversation_history

    try:
        # Ajouter le prompt de l'utilisateur à l'historique
        conversation_history.append({"role": "user", "content": prompt})

        # Préparer le contexte complet pour l'API
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        # Envoi de la requête au modèle (API)
        res = requests.post(
            'http://ollama:11434/api/generate',
            json={
                "prompt": context,
                "stream": True,
                "model": "llama3.2:1b",
            },
            headers={"Content-Type": "application/json"},
            stream=True
        )

        if res.status_code != 200:
            return StreamingResponse(
                iter([f"Error: Unexpected status code {res.status_code}"]),
                media_type="text/plain"
            )

        def generate():
            buffer = ""
            full_response = ""
            for chunk in res.iter_content(chunk_size=16):
                if chunk:
                    buffer += chunk.decode('utf-8')
                    while '}' in buffer:
                        try:
                            end = buffer.index('}') + 1
                            data = json.loads(buffer[:end])
                            if "response" in data:
                                response_chunk = data["response"]
                                full_response += response_chunk
                                yield response_chunk
                            buffer = buffer[end:]
                        except json.JSONDecodeError:
                            break

            # Ajouter la réponse complète à l'historique de la conversation
            conversation_history.append({"role": "assistant", "content": full_response})

        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        return StreamingResponse(
            iter([f"Error: {str(e)}"]),
            media_type="text/plain"
        )

