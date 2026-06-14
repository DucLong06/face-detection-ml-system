variable "credentials" {
  description = "Path to the GCP service account key file"
  type        = string
  sensitive   = true
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for resources"
  type        = string
}

variable "zone" {
  description = "GCP Zone for resources"
  type        = string
}

# GKE Variables
variable "machine_type_node" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-medium"
}

# Compute Instance Variables
variable "instance_name" {
  description = "Name for the Jenkins instance"
  type        = string
  default     = "jenkins-server"
}

variable "machine_type_instance" {
  description = "Machine type for Jenkins instance"
  type        = string
  default     = "e2-medium"
}

variable "boot_disk_image" {
  description = "Boot disk image for Jenkins instance"
  type        = string
  default     = "ubuntu-os-cloud/ubuntu-2004-lts"
}

variable "boot_disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 50
}

variable "firewall_name" {
  description = "Name for the firewall rule"
  type        = string
  default     = "jenkins-firewall"
}

variable "user_name" {
  description = "SSH public key for Jenkins instance"
  type        = string
  sensitive   = true
  default     = "longhd"
}