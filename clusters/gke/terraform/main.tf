
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "4.80.0" // Provider version
    }
  }
  required_version = "1.10.3" // Terraform version
}

provider "google" {
  credentials = var.credentials
  project     = var.project_id
  region      = var.region
}

# Google Kubernetes Engine
resource "google_container_cluster" "gke_face" {
  name                     = "${var.project_id}-gke"
  location                 = var.region
  remove_default_node_pool = true
  initial_node_count       = 1

  node_config {
    disk_type    = "pd-standard"
    disk_size_gb = 50
  }
}

resource "google_container_node_pool" "gke_nodes-face" {
  name       = "my-node-pool"
  location   = var.region
  cluster    = google_container_cluster.gke_face.name
  node_count = 1
  
  node_config {
    preemptible  = true
    machine_type = var.machine_type_node
    disk_type    = "pd-standard"
    disk_size_gb = 50
  }
}

# Google compute instance
resource "google_compute_instance" "instance_jenkins" {
  name         = var.instance_name
  machine_type = var.machine_type_instance
  zone         = var.zone
  tags         = [var.firewall_name]

  boot_disk {
    initialize_params {
      image = var.boot_disk_image
      size  = var.boot_disk_size
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral public IP
    }
  }
 
   metadata = {
    ssh-keys = "${var.user_name}:${file("${path.module}/../ssh_keys/jenkins_key.pub")}"
  }

  // save the public key in a local variable for ansible setup jenkins
  provisioner "local-exec" {
    command = <<-EOT
      echo "[jenkins]" > ${path.module}/../ansible/inventory/inventory.ini
      echo "${self.network_interface[0].access_config[0].nat_ip} ansible_user=${var.user_name} ansible_ssh_private_key_file=${path.module}/../ssh_keys/jenkins_key" >> ${path.module}/../ansible/inventory/inventory.ini
    EOT
  } 
}

resource "google_compute_firewall" "firewall_jenkins" {
  name          = var.firewall_name
  network       = "default"
  target_tags   = [var.firewall_name]
  
  allow {
    protocol = "tcp"
    ports    = ["8080", "50000"]
  }
  
  source_ranges = ["0.0.0.0/0"]
}