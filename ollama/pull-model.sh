#!/bin/sh

./bin/ollama serve &

pid=$!
sleep 5

echo "Pulling mistral model"
ollama pull mistral

wait $pid