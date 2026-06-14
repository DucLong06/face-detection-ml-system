locals {
  ssh_pub_key = file("${path.module}/../ssh_keys/jenkins_key.pub")
}