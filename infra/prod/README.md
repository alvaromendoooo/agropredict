# agro-predict-infra

Infraestructura como Código (IaC) para el proyecto [Agro Predict](https://github.com/agro-predict-tfg-2026).

Define y provisiona toda la infraestructura necesaria en AWS usando Terraform.
El entorno `local` apunta a LocalStack para desarrollo sin coste.
El entorno `production` apunta a AWS real (free tier).

## Estructura

```
agro-predict-infra/
├── modules/                  # Módulos reutilizables por entorno
│   ├── networking/           # VPC, subnets, security groups
│   ├── compute/              # Instancia EC2 donde corre docker-compose
│   ├── storage/              # Bucket S3 para logs de alertas
│   └── secrets/              # Secrets Manager para API keys
├── environments/
│   ├── local/                # Apunta a LocalStack (desarrollo)
│   └── production/           # Apunta a AWS real
└── scripts/
    └── start-localstack.sh   # Levanta LocalStack con Docker
```

## Requisitos

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [Docker](https://docs.docker.com/get-docker/) (para LocalStack)
- [AWS CLI](https://aws.amazon.com/cli/) (opcional, para inspeccionar recursos)

## Entorno local con LocalStack

```bash
# 1. Levantar LocalStack
./scripts/start-localstack.sh

# 2. Inicializar y aplicar Terraform
cd environments/local
terraform init
terraform apply

# 3. Para destruir los recursos
terraform destroy
```

## Entorno de producción (AWS real)

```bash
# Configura tus credenciales de AWS
aws configure

cd environments/production
terraform init
terraform apply
```

## Módulos

| Módulo       | Descripción                                              |
|--------------|----------------------------------------------------------|
| `networking` | VPC, subnet pública, internet gateway, security group    |
| `compute`    | Instancia EC2 con Docker instalado via user_data         |
| `storage`    | Bucket S3 para almacenar logs de alertas de heladas      |
| `secrets`    | Secrets Manager con las API keys de AEMET, SiAR, ITACyL  |
