#!/bin/sh

./bin/ollama serve &

pid=$!

sleep 5


echo "Pulling llama3.2 model"
ollama pull llama3.2:1b


wait $pid
