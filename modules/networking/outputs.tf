# modules/networking/outputs.tf
# Los outputs exponen valores del módulo para que otros módulos los usen.
# Por ejemplo, compute necesita saber el ID de la subnet y del security group.

output "vpc_id" {
  description = "ID de la VPC creada"
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "ID de la subnet pública"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "ID del security group de Agro Predict"
  value       = aws_security_group.agro_predict.id
}
