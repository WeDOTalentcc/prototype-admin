output "instance_ip" {
  description = "IP público da instância EC2."
  value       = aws_instance.lia_api.public_ip
}

output "instance_id" {
  description = "ID da instância EC2 criada."
  value       = aws_instance.lia_api.id
}

output "ecr_url" {
  description = "URL do repositório ECR (sem tag)."
  value       = aws_ecr_repository.lia.repository_url
}

output "security_group_id" {
  description = "ID do Security Group criado para a API."
  value       = aws_security_group.lia_api.id
}
