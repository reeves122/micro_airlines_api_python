resource "aws_api_gateway_rest_api" "api" {
  name = "${var.name}-${var.env}"
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    aws_api_gateway_rest_api.api,
    aws_api_gateway_integration.get,
    aws_api_gateway_integration.post,
    aws_api_gateway_integration.put
  ]

  rest_api_id       = aws_api_gateway_rest_api.api.id
  stage_name        = var.env
  stage_description = "Deployed ${timestamp()}"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_resource" "root_proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}
