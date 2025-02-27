from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import requests
import json
import time
import httpx
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conversion de la fonction en asynchrone
    await wait_for_ollama_tag(), health_check()
    yield

app = FastAPI(lifespan=lifespan)



templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

conversation_history = []

# Modification de la fonction pour la rendre asynchrone
async def wait_for_ollama_tag():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get('http://ollama:11434/api/tags', timeout=55)
                
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [model.get('name', '') for model in models]
                    print("Modèles disponibles:", model_names)
                    
                    # Vérification plus précise du nom du modèle
                    target_model = "MrSplatchy/Cookama:latest"
                    if any(target_model in name for name in model_names):
                        print(f"Modèle {target_model} trouvé. Démarrage de l'application.")
                        return
                    else:
                        print(f"Modèle {target_model} non trouvé dans la liste: {model_names}")
                else:
                    print(f"Erreur de réponse: {response.status_code}")

        except Exception as e:
            print(f"Erreur lors de la vérification du modèle: {str(e)}. Nouvelle tentative dans 10s...")

        await asyncio.sleep(10)

@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def ask(request: Request, prompt: str = Form(...)):
    global conversation_history
    conversation_history = conversation_history[-8:]

    conversation_history.append({"role": "user", "content": prompt})

    try:
        res = requests.post(
            'http://ollama:11434/api/generate',
            json={
                "prompt": "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history]),
                "stream": True,
                # Modification ici ↓
                "model": "MrSplatchy/Cookama:latest",
                "options": {
                    "temperature": 0.5,
                    "num_predict": 200,
                    "num_threads": 8,
                    "keep_alive": 300
                }
            },
            headers={"Content-Type": "application/json"},
            stream=True
        )

        def generate():
            full_response = ""

            for line in res.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            response_chunk = data["response"]
                            full_response += response_chunk
                            yield response_chunk
                            
                    except json.JSONDecodeError:
                        continue

            conversation_history.append({"role": "assistant", "content": full_response})

        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        return StreamingResponse(iter([f"Error: {str(e)}"]), media_type="text/plain")


@app.get("/health")
async def health_check():
    while True:
        return {"status": "ok"}

