terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# ---------------------------------------------------------------------------
# Security Group — portas 22, 8000, 443 inbound; egress irrestrito
# Equivalente a `aws ec2 create-security-group` + authorize-security-group-ingress
# ---------------------------------------------------------------------------
resource "aws_security_group" "lia_api" {
  name        = "lia-agent-api-sg"
  description = "LIA Agent System API"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "LIA API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Egress irrestrito"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lia-agent-api-sg"
  }
}

# ---------------------------------------------------------------------------
# ECR Repository — lia-agent-system com scan on push
# Equivalente a `aws ecr create-repository` em aws_setup.sh
# ---------------------------------------------------------------------------
resource "aws_ecr_repository" "lia" {
  name                 = "lia-agent-system"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "lia-agent-system"
  }
}

# ---------------------------------------------------------------------------
# AMI data source — Amazon Linux 2023 mais recente
# Equivalente à resolução automática de AMI em aws_setup.sh
# ---------------------------------------------------------------------------
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# ---------------------------------------------------------------------------
# EC2 instance — t3.xlarge, Amazon Linux 2023, user-data Docker
# Equivalente a `aws ec2 run-instances` em aws_setup.sh
# ---------------------------------------------------------------------------
resource "aws_instance" "lia_api" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.lia_api.id]
  user_data              = file("${path.module}/userdata.sh")

  tags = {
    Name = "lia-agent-api"
  }
}
