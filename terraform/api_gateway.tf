resource "aws_api_gateway_rest_api" "this" {
  name = local.name
}

resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.this.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.root_proxy.id,

      aws_api_gateway_method.get.id,
      aws_api_gateway_method.put.id,
      aws_api_gateway_method.post.id,
      aws_api_gateway_method.options.id,

      aws_api_gateway_integration.get.id,
      aws_api_gateway_integration.put.id,
      aws_api_gateway_integration.post.id,
      aws_api_gateway_integration.options.id,

    ]))
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "this" {
  deployment_id = aws_api_gateway_deployment.this.id
  rest_api_id   = aws_api_gateway_rest_api.this.id
  stage_name    = "this"
}

resource "aws_api_gateway_resource" "root_proxy" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = "{proxy+}"
}
