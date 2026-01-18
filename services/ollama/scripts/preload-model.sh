#!/bin/sh

echo "Iniciando Ollama..."
ollama serve &
OLLAMA_PID=$!

# Esperar a que Ollama realmente esté listo
echo "Esperando a que Ollama esté listo..."
until curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do
    sleep 1
done

echo "Precargando el modelo qwen2.5:7b..."
ollama pull qwen2.5:7b

# Mantener el modelo cargado en memoria
echo "Cargando modelo en memoria..."
echo "Ping" | ollama run qwen2.5:7b --keepalive 60m >/dev/null 2>&1 &

echo "Servidor Ollama en ejecución."
wait $OLLAMA_PID
