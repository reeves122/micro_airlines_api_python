locals {
  region     = data.aws_region.this.name
  name       = "micro_airlines_api_${random_string.this.result}"
  lambda_uri = "arn:aws:apigateway:${local.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.this.arn}/invocations"
}
