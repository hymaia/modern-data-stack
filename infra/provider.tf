terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
    helm = {
      source  = "hashicorp/helm"
    }
  }

  backend "s3" {
    bucket         = "hyma-kube-terraform-state-management-dev"
    key            = "terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
  }
}

provider "aws" {
  region = "eu-west-1"

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

provider "helm" {
  kubernetes {
    host                   = module.kubernetes.cluster[0].cluster_endpoint
    cluster_ca_certificate = base64decode(module.kubernetes.cluster[0].cluster_certificate_authority_data)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.kubernetes.cluster[0].cluster_name]
    }
  }
}
