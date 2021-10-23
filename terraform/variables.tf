variable "account" {}
variable "region" {}
variable "env" {}

variable "name" {
  default = "micro_airlines_api"
}

resource "random_string" "bucket_suffix" {
  length = 8
  lower = true
  upper = false
  special = false
}

locals {
  bucket_name = "micro-airlines-api-${var.env}-${random_string.bucket_suffix.result}"
  lambda_uri = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.micro_airlines_api_lambda.arn}/invocations"
}
