resource "aws_lambda_function" "micro_airlines_api_lambda" {
  filename      = "../package.zip"
  function_name = "${var.name}-${var.env}"
  role          = "${aws_iam_role.micro_airlines_api_lambda_role.arn}"
  handler       = "micro_airlines_api.lambda_handler"
  runtime       = "python3.7"
  timeout       = "5"
  memory_size   = 128

  source_code_hash = "${filebase64sha256("../package.zip")}"

  environment {
    variables = {
      DYNAMODB_PLAYERS_TABLE             = "${var.name}-players-${var.env}"
    }
  }
}

resource "aws_iam_role" "micro_airlines_api_lambda_role" {
  name = "${var.name}-${var.env}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "micro_airlines_api_lambda_role_policy" {
  name = "${var.name}-${var.env}"
  role = "${aws_iam_role.micro_airlines_api_lambda_role.id}"

  policy = <<EOF
{
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:DeleteItem",
                "dynamodb:UpdateItem",
                "dynamodb:Scan",
                "dynamodb:Query"
            ],
            "Resource": [
                "${aws_dynamodb_table.players_table.arn}",
                "${aws_dynamodb_table.players_table.arn}*"
            ]
        }
    ]
}
    EOF
}

resource "aws_cloudwatch_log_group" "lambda_proxy_log_group" {
  name              = "/aws/lambda/${var.name}-${var.env}"
  retention_in_days = "3"
}

