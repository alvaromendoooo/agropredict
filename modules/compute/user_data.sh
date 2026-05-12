#!/bin/bash
# user_data.sh
# Se ejecuta automáticamente cuando la instancia EC2 arranca por primera vez.
# Instala Docker, clona el repo de orquestación y lanza los servicios.

set -e
exec > /var/log/user-data.log 2>&1  # redirige logs para poder depurar

echo "=== Instalo dependencias para correr docker ==="
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "$${UBUNTU_CODENAME:-$$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl status docker

sudo systemctl start docker


echo "=== Clonando repositorio de orquestación ==="
git clone https://github.com/${github_org}/agro-predict-orchestator.git /opt/agro-predict

echo "=== Construcción del .env del que dependerán los contenedores"
cat > /opt/agro-predict/no-gpu/.env <<EOF
${orchestator_env}
EOF

echo "=== Lanzando servicios con Docker Compose ==="
cd /opt/agro-predict
docker compose pull
docker compose up -d

echo "=== Agro Predict desplegado correctamente ==="
