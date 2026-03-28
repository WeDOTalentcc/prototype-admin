variable "region" {
  description = "Região AWS onde os recursos serão criados."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Tipo de instância EC2. Padrão t3.xlarge (4 vCPU, 16 GB RAM)."
  type        = string
  default     = "t3.xlarge"
}

variable "image_tag" {
  description = "Tag da imagem Docker usada no user-data e nos scripts de deploy."
  type        = string
  default     = "latest"
}
