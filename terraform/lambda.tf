resource "aws_lambda_function" "this" {
  filename      = "package.zip"
  function_name = local.name
  role          = aws_iam_role.lambda.arn
  handler       = "micro_airlines_api.lambda_handler"
  runtime       = "python3.7"
  timeout       = "5"
  memory_size   = 128

  source_code_hash = filebase64sha256("package.zip")

  environment {
    variables = {
      DYNAMODB_PLAYERS_TABLE = aws_dynamodb_table.players.name
    }
  }
}

