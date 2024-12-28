import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()

# Configuration de Jinja2 et des fichiers statiques
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    """Affiche le formulaire pour entrer un prompt."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def ask(request: Request, prompt: str = Form(...)):
    """Traitement du prompt et affichage du résultat en streaming."""
    
    try:
        res = requests.post(
            'http://ollama:11434/api/generate',
            json={
                "prompt": prompt,
                "stream": True,
                "model": "mistral"
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
            try:
                buffer = ""
                for chunk in res.iter_content(chunk_size=64):
                    if chunk:
                        buffer += chunk.decode('utf-8')
                        print(f"Chunk received: {buffer}")  # Log des données reçues
                        try:
                            data = json.loads(buffer)
                            if "response" in data:
                                yield data["response"]
                                buffer = ""
                        except json.JSONDecodeError:
                            # Gérer les données partiellement valides
                            if '}' in buffer:
                                parts = buffer.rsplit('}', 1)
                                try:
                                    data = json.loads(parts[0] + '}')
                                    yield data["response"]
                                    buffer = parts[1]  # Conserver les restes
                                except json.JSONDecodeError:
                                    pass  # Ignorer si ce n'est pas encore valide
            except Exception as e:
                yield f"Error: {str(e)}"

        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        return StreamingResponse(
            iter([f"Error: {str(e)}"]),
            media_type="text/plain"
        )
