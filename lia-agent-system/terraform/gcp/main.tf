terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ---------------------------------------------------------------------------
# VM instance — e2-standard-4, Debian 12, pd-ssd 50 GB
# Equivalente a `gcloud compute instances create` em gcp_setup.sh
# ---------------------------------------------------------------------------
resource "google_compute_instance" "lia_api" {
  name         = var.vm_name
  machine_type = "e2-standard-4"
  zone         = var.zone
  tags         = ["http-server", "https-server", "lia-api"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 50
      type  = "pd-ssd"
    }
  }

  network_interface {
    network = "default"
    access_config {}  # IP público efêmero
  }

  metadata_startup_script = file("${path.module}/startup.sh")

  service_account {
    scopes = ["cloud-platform"]
  }
}

# ---------------------------------------------------------------------------
# Firewall — permite TCP 8000 e 443 para instâncias com tag lia-api
# Equivalente a `gcloud compute firewall-rules create allow-lia-api`
# ---------------------------------------------------------------------------
resource "google_compute_firewall" "allow_lia_api" {
  name    = "allow-lia-api"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8000", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["lia-api"]
}

# ---------------------------------------------------------------------------
# Container Registry (GCR)
# Equivalente ao uso de gcr.io/${PROJECT_ID}/lia-agent-system em gcp_setup.sh
# ---------------------------------------------------------------------------
resource "google_container_registry" "lia" {
  location = "US"
}
