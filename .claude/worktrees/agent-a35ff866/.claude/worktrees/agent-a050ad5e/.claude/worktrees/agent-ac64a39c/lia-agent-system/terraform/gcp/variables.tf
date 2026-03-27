variable "project_id" {
  description = "ID do projeto GCP. Obrigatório — sem valor padrão."
  type        = string
}

variable "region" {
  description = "Região GCP onde os recursos serão criados."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zona GCP onde a VM será criada."
  type        = string
  default     = "us-central1-a"
}

variable "vm_name" {
  description = "Nome da instância Compute Engine."
  type        = string
  default     = "lia-agent-vm"
}

variable "image_tag" {
  description = "Tag da imagem Docker a ser usada no startup script."
  type        = string
  default     = "latest"
}
