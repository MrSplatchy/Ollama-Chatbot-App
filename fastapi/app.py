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

# Class-level variable to store the previous prompt
previous_prompt = ""

@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    """Affiche le formulaire pour entrer un prompt."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def ask(request: Request, prompt: str = Form(...)):
    """Traitement du prompt et affichage du résultat en streaming."""
    
    global previous_prompt
    
    try:
        # Combine the previous prompt and the current prompt for context
        combined_prompt = f"{previous_prompt}\n{prompt}"
        
        res = requests.post(
            'http://ollama:11434/api/generate',
            json={
                "prompt": combined_prompt,
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
            for chunk in res.iter_content(chunk_size=16):  # Increased chunk size for efficiency
                if chunk:
                    buffer += chunk.decode('utf-8')
                    while '}' in buffer:
                        try:
                            end = buffer.index('}') + 1
                            data = json.loads(buffer[:end])
                            if "response" in data:
                                # Update the previous prompt with the response
                                previous_prompt = data["response"]
                                yield data["response"]
                            buffer = buffer[end:]
                        except json.JSONDecodeError:
                            break  # Wait for more data if JSON is incomplete
            
            # Process any remaining data in the buffer
            if buffer:
                try:
                    data = json.loads(buffer)
                    if "response" in data:
                        # Update the previous prompt with the response
                        previous_prompt = data["response"]
                        yield data["response"]
                except json.JSONDecodeError:
                    pass  # Ignore if the remaining data is not valid JSON


        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        return StreamingResponse(
            iter([f"Error: {str(e)}"]),
            media_type="text/plain"
        )