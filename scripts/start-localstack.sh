#!/bin/bash
# start-localstack.sh
# Levanta LocalStack en Docker con los servicios necesarios para Agro Predict

set -e

SERVICES="s3,secretsmanager,ec2"
LOCALSTACK_IMAGE="localstack/localstack:3.0"

echo "🚀 Levantando LocalStack con servicios: $SERVICES"

docker run -d \
  --name localstack-agro \
  -p 4566:4566 \
  -e SERVICES=$SERVICES \
  -e DEFAULT_REGION=us-east-1 \
  -e DEBUG=0 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  $LOCALSTACK_IMAGE

echo "⏳ Esperando a que LocalStack esté listo..."
until curl -s http://localhost:4566/_localstack/health | grep -q '"s3": "available"'; do
  sleep 2
done

echo "✅ LocalStack listo en http://localhost:4566"
echo ""
echo "Para parar LocalStack:"
echo "  docker stop localstack-agro && docker rm localstack-agro"
