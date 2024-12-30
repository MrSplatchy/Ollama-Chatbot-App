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
                "model": "mistral",
                "options": {
            "n_ctx_per_seq": 8192  #U can adjust this value as needed
                }
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
            for chunk in res.iter_content(chunk_size=16):  # Increased chunk size for efficiency
                if chunk:
                    buffer += chunk.decode('utf-8')
                    while '}' in buffer:
                        try:
                            end = buffer.index('}') + 1
                            data = json.loads(buffer[:end])
                            if "response" in data:
                                yield data["response"]
                            buffer = buffer[end:]
                        except json.JSONDecodeError:
                            break  # Wait for more data if JSON is incomplete
            
            # Process any remaining data in the buffer
            if buffer:
                try:
                    data = json.loads(buffer)
                    if "response" in data:
                        yield data["response"]
                except json.JSONDecodeError:
                    pass  # Ignore if the remaining data is not valid JSON


        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        return StreamingResponse(
            iter([f"Error: {str(e)}"]),
            media_type="text/plain"
        )
