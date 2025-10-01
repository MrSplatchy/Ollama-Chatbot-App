#!/bin/sh

./bin/ollama serve &

pid=$!
sleep 5

echo "Pulling Cookama"
./bin/ollama pull MrSplatchy/Cookama

# Vérification que le modèle est bien présent
echo "Vérification du modèle"
./bin/ollama list

wait $pid