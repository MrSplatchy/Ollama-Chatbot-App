# Utilise une image Python légère
FROM python:3.12-slim

# Configure l'environnement de travail
WORKDIR /app

# Copie les fichiers nécessaires
COPY ./app /app

# Copie le fichier requirements.txt
COPY requirements.txt /app/

# Installe les dépendances
RUN pip install  -r requirements.txt

# Expose le port utilisé par FastAPI
EXPOSE 8000

# Commande pour lancer l'application
CMD ["uvicorn", "app:app"]
