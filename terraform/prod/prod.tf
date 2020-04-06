terraform {
  backend "s3" {
    bucket  = "micro-airlines-api-prod-m2fcawsy"
    key     = "micro_airlines_api/prod-810826485769"
    region  = "us-east-1"
    encrypt = true
    profile = "810826485769"
  }
}

locals {
  region  = "us-east-1"
  account = "810826485769"
}

provider "aws" {
  region  = "${local.region}"
  profile = "${local.account}"
  version = "~> 2.49"
}

module "terraform" {
  source  = "../"
  region  = "${local.region}"
  account = "${local.account}"
  env     = "prod"
}
