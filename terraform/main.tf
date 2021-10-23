terraform {
  backend "s3" {}
}

resource "random_string" "this" {
  length  = 6
  lower   = true
  upper   = false
  special = false
}

data "aws_region" "this" {}