#!/bin/bash
# user_data.sh
# Se ejecuta automáticamente cuando la instancia EC2 arranca por primera vez.
# Instala Docker, clona el repo de orquestación y lanza los servicios.

set -e
exec > /var/log/user-data.log 2>&1  # redirige logs para poder depurar

echo "=== Instalando Docker ==="
apt-get update -y
apt-get install -y docker.io docker-compose-plugin git curl

systemctl enable docker
systemctl start docker

# Añadir usuario ubuntu al grupo docker (evita usar sudo)
usermod -aG docker ubuntu

echo "=== Clonando repositorio de orquestación ==="
git clone https://github.com/${github_org}/agro-predict-orchestator.git /opt/agro-predict
cd /opt/agro-predict

echo "=== Construcción del .env del que dependerán los contenedores"
cat > agro-predict-orchestator/docker/.env <<EOF
${orchestator_env}
EOF

echo "=== Lanzando servicios con Docker Compose ==="
docker compose pull
docker compose up -d

echo "=== Agro Predict desplegado correctamente ==="
