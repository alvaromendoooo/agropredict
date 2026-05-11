# modules/compute/outputs.tf

output "instance_id" {
  description = "ID de la instancia EC2"
  value       = aws_instance.agro_predict.id
}

output "public_ip" {
  description = "IP pública de la instancia"
  value       = aws_instance.agro_predict.public_ip
}
