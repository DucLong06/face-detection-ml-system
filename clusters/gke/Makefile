# Variables
SHELL := /bin/bash
SSH_KEY_DIR := ssh_keys
SSH_KEY_PATH := $(SSH_KEY_DIR)/jenkins_key
TERRAFORM_DIR := terraform
ANSIBLE_DIR := ansible
INVENTORY_FILE := $(ANSIBLE_DIR)/inventory/inventory.ini
JENKINS_IMAGE := longhd06/jenkins-docker-helm
JENKINS_TAG := latest
REQUIRED_DIRS := $(SSH_KEY_DIR) $(TERRAFORM_DIR) $(ANSIBLE_DIR)

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
NC := \033[0m

# Default target
.PHONY: all
all: help

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make check-dirs            - Check and create required directories"
	@echo "  make build-push-image      - Build Jenkins Docker image"
	@echo "  make push-image            - Push Jenkins image to DockerHub"
	@echo "  make generate-key          - Generate SSH key pair"
	@echo "  make init                  - Initialize Terraform"
	@echo "  make plan                  - Run Terraform plan"
	@echo "  make apply                 - Apply Terraform configuration"
	@echo "  make deploy                - Deploy Jenkins using Ansible"
	@echo "  make all-in-one            - Run complete deployment pipeline"
	@echo "  make destroy               - Destroy infrastructure"
	@echo "  make clean                 - Clean up local files"

# Check and create required directories
.PHONY: check-dirs
check-dirs:
	@echo -e "$(GREEN)Checking required directories...$(NC)"
	@for dir in $(REQUIRED_DIRS); do \
		if [ ! -d $$dir ]; then \
			echo -e "$(YELLOW)Creating directory: $$dir$(NC)"; \
			mkdir -p $$dir; \
		else \
			echo -e "$(GREEN)Directory exists: $$dir$(NC)"; \
		fi; \
	done
	@echo -e "$(GREEN)Directory check complete$(NC)"

# Check SSH key permissions
.PHONY: check-ssh-perms
check-ssh-perms:
	@if [ -f $(SSH_KEY_PATH) ]; then \
		chmod 600 $(SSH_KEY_PATH); \
		chmod 644 $(SSH_KEY_PATH).pub; \
		echo -e "$(GREEN)SSH key permissions set correctly$(NC)"; \
	fi

# Build Jenkins Docker image
.PHONY: build-push-image
build-push-image:
	@echo -e "$(GREEN)Building Jenkins Docker image...$(NC)"
	cd custom_images/jenkins && ./build.sh

# Push image to registry
.PHONY: push-image
push-image:
	@echo -e "$(GREEN)Pushing image to DockerHub...$(NC)"
	docker push $(JENKINS_IMAGE):$(JENKINS_TAG)

# Generate SSH key pair
.PHONY: generate-key
generate-key: check-dirs
	@echo -e "$(GREEN)Generating SSH key pair...$(NC)"
	@if [ ! -f $(SSH_KEY_PATH) ]; then \
		ssh-keygen -t rsa -b 2048 -f $(SSH_KEY_PATH) -C "longhd" -N ""; \
		echo -e "$(GREEN)SSH key pair generated successfully$(NC)"; \
	else \
		echo -e "$(YELLOW)SSH key already exists at $(SSH_KEY_PATH)$(NC)"; \
	fi
	@$(MAKE) check-ssh-perms

# Initialize Terraform
.PHONY: init
init: check-dirs
	@echo -e "$(GREEN)Initializing Terraform...$(NC)"
	cd $(TERRAFORM_DIR) && terraform init

# Plan Terraform changes
.PHONY: plan
plan: init
	@echo -e "$(GREEN)Planning Terraform changes...$(NC)"
	cd $(TERRAFORM_DIR) && terraform plan

# Apply Terraform configuration
.PHONY: apply
apply: init
	@echo -e "$(GREEN)Applying Terraform configuration...$(NC)"
	cd $(TERRAFORM_DIR) && terraform apply -auto-approve

# Deploy Jenkins using Ansible
.PHONY: deploy
deploy:
	@echo -e "$(GREEN)Deploying Jenkins using Ansible...$(NC)"
	@if [ ! -f $(INVENTORY_FILE) ]; then \
		echo -e "$(RED)Error: Inventory file not found at $(INVENTORY_FILE)$(NC)"; \
		exit 1; \
	fi
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/deploy_jenkins.yaml

# Complete deployment pipeline
.PHONY: all-in-one
all-in-one: check-dirs generate-key build-push-image push-image apply deploy
	@echo -e "$(GREEN)Complete deployment finished!$(NC)"

# Destroy infrastructure
.PHONY: destroy
destroy:
	@echo -e "$(GREEN)Destroying infrastructure...$(NC)"
	cd $(TERRAFORM_DIR) && terraform destroy -auto-approve

# Clean up
.PHONY: clean
clean:
	@echo -e "$(GREEN)Cleaning up...$(NC)"
	-rm -f $(TERRAFORM_DIR)/.terraform.lock.hcl
	-rm -rf $(TERRAFORM_DIR)/.terraform
	-rm -f $(TERRAFORM_DIR)/terraform.tfstate*