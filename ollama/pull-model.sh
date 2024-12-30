#!/bin/sh

./bin/ollama serve &

pid=$!
sleep 5

echo "Pulling mistral model"
ollama pull llama3.2:1

wait $pid