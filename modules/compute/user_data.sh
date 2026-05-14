#!/bin/bash
# user_data.sh
# Se ejecuta automáticamente cuando la VM arranca por primera vez.
# Instala Docker, clona el repo de orquestación y lanza los servicios.

set -e
exec > /var/log/user-data.log 2>&1  # redirige logs para poder depurar

echo "=== Instalando dependencias para Docker ==="
apt-get update -y
apt-get install -y ca-certificates curl git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$${VERSION_CODENAME}") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

echo "=== Clonando repositorio de orquestación ==="
git clone https://github.com/${github_org}/agro-predict-orchestator.git /opt/agro-predict

echo "=== Construcción del .env del que dependerán los contenedores ==="
cat > /opt/agro-predict/no-gpu/.env <<EOF
${orchestator_env}
EOF

echo "=== Lanzando servicios con Docker Compose ==="
cd /opt/agro-predict/no-gpu
docker compose pull
docker compose up -d

echo "=== Agro Predict desplegado correctamente ==="
