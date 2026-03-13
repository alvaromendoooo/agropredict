#!/bin/sh

echo "Iniciando Ollama..."
ollama serve &
OLLAMA_PID=$!

# Esperar activamente a que Ollama esté listo
echo "Esperando a que Ollama esté disponible..."
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
  sleep 1
done

echo "Precargando el modelo qwen2.5:7b..."
ollama pull qwen2.5:7b

echo "Servidor Ollama en ejecución."

# Esperar al proceso original (no relanzar un segundo serve)
wait $OLLAMA_PID