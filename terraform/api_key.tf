resource "aws_api_gateway_api_key" "admin" {
  name = "admin"
}

resource "aws_api_gateway_usage_plan" "admin" {
  name = "admin"

  api_stages {
    api_id = aws_api_gateway_rest_api.this.id
    stage  = aws_api_gateway_deployment.this.stage_name
  }

  throttle_settings {
    burst_limit = "10"
    rate_limit  = "5"
  }
}

resource "aws_api_gateway_usage_plan_key" "admin" {
  key_id        = aws_api_gateway_api_key.admin.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.admin.id
}