resource "aws_api_gateway_rest_api" "api" {
  name = "${var.name}-${var.env}"
}

resource "aws_iam_role" "invocation_role" {
  name = "${var.name}-role-${var.env}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "invocation_policy" {
  name = "${var.name}-role-policy-${var.env}"
  role = "${aws_iam_role.invocation_role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "lambda:InvokeFunction",
      "Effect": "Allow",
      "Resource": [
        "${aws_lambda_function.micro_airlines_api_lambda.arn}"
      ]
    }
  ]
}
EOF
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    "aws_api_gateway_rest_api.api",
    "aws_api_gateway_integration.root_GET",
    "aws_api_gateway_integration.root_POST",
    "aws_api_gateway_integration.root_PUT"
  ]

  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  stage_name  = "${var.env}"
  stage_description = "Deployed ${timestamp()}"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_resource" "root_proxy" {
  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  parent_id   = "${aws_api_gateway_rest_api.api.root_resource_id}"
  path_part = "{proxy+}"
}

# GET
resource "aws_api_gateway_method" "root_GET" {
  rest_api_id      = "${aws_api_gateway_rest_api.api.id}"
  resource_id      = "${aws_api_gateway_resource.root_proxy.id}"
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "root_GET" {
  rest_api_id             = "${aws_api_gateway_rest_api.api.id}"
  resource_id             = "${aws_api_gateway_resource.root_proxy.id}"
  http_method             = "${aws_api_gateway_method.root_GET.http_method}"
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.micro_airlines_api_lambda.arn}/invocations"
  credentials             = "${aws_iam_role.invocation_role.arn}"
}

# POST
resource "aws_api_gateway_method" "root_POST" {
  rest_api_id      = "${aws_api_gateway_rest_api.api.id}"
  resource_id      = "${aws_api_gateway_resource.root_proxy.id}"
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "root_POST" {
  rest_api_id             = "${aws_api_gateway_rest_api.api.id}"
  resource_id             = "${aws_api_gateway_resource.root_proxy.id}"
  http_method             = "${aws_api_gateway_method.root_POST.http_method}"
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.micro_airlines_api_lambda.arn}/invocations"
  credentials             = "${aws_iam_role.invocation_role.arn}"
}

# PUT
resource "aws_api_gateway_method" "root_PUT" {
  rest_api_id      = "${aws_api_gateway_rest_api.api.id}"
  resource_id      = "${aws_api_gateway_resource.root_proxy.id}"
  http_method      = "PUT"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "root_PUT" {
  rest_api_id             = "${aws_api_gateway_rest_api.api.id}"
  resource_id             = "${aws_api_gateway_resource.root_proxy.id}"
  http_method             = "${aws_api_gateway_method.root_PUT.http_method}"
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.micro_airlines_api_lambda.arn}/invocations"
  credentials             = "${aws_iam_role.invocation_role.arn}"
}
