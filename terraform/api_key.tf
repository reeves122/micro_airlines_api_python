resource "aws_api_gateway_api_key" "admin_key" {
  name = "admin"
}

resource "aws_api_gateway_usage_plan" "admin_plan" {
  name = "admin"

  api_stages {
    api_id = aws_api_gateway_rest_api.api.id
    stage  = aws_api_gateway_deployment.deployment.stage_name
  }

  throttle_settings {
    burst_limit = "10"
    rate_limit  = "5"
  }
}

resource "aws_api_gateway_usage_plan_key" "admin_plan_key" {
  key_id        = aws_api_gateway_api_key.admin_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.admin_plan.id
}