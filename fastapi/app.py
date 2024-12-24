import requests
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Configuration de Jinja2 et des fichiers statiques
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    """Affiche le formulaire pour entrer un prompt."""
    
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
def ask(request: Request, prompt: str = Form(...)):
    """Traitement du prompt et affichage du résultat."""
    
    res = requests.post('http://ollama:11434/api/generate', json={
        "prompt": prompt,
        "stream": False,
        "model": "llama3.2:1b"
    })

        # Extraire uniquement la valeur de la clé 'text'
    try:
        generated_text = res.json().get("response", "No response found")
    except ValueError:
        return Response(content="Invalid JSON response", media_type="text/plain")

    # Retourne la réponse dans la page
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "prompt": prompt,
            "response": generated_text
        }
    )
