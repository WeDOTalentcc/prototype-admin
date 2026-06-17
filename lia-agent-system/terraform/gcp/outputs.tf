output "vm_ip" {
  description = "IP público externo da VM (ephemeral)."
  value       = google_compute_instance.lia_api.network_interface[0].access_config[0].nat_ip
}

output "vm_name" {
  description = "Nome da instância Compute Engine criada."
  value       = google_compute_instance.lia_api.name
}

output "registry_url" {
  description = "URL base do Google Container Registry para o projeto."
  value       = "gcr.io/${var.project_id}/lia-agent-system"
}
