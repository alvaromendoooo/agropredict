Write-Host "Iniciando Ollama..."
ollama serve
$OLLAMA_PID=$!

Write-Host "Esperando a que Ollama esté listo"
Start-Sleep 5

Write-Host "Procesando el modelo qwen2.5:7b..."
ollama pull qwen2.5:7b

# Mantener el modelo en memoria
ollama run qwen2.5:7b --keepalive 60m "" &

# Mantener el proceso principal
wait $OLLAMA_PID
