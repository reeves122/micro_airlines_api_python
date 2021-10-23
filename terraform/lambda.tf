resource "aws_lambda_function" "micro_airlines_api_lambda" {
  filename      = "../package.zip"
  function_name = "${var.name}-${var.env}"
  role          = aws_iam_role.micro_airlines_api_lambda_role.arn
  handler       = "micro_airlines_api.lambda_handler"
  runtime       = "python3.7"
  timeout       = "5"
  memory_size   = 128

  source_code_hash = filebase64sha256("../package.zip")

  environment {
    variables = {
      DYNAMODB_PLAYERS_TABLE             = "${var.name}-players-${var.env}"
    }
  }
}

