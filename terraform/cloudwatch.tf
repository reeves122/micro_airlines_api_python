resource "aws_cloudwatch_log_group" "lambda_proxy_log_group" {
  name              = "/aws/lambda/${var.name}-${var.env}"
  retention_in_days = "3"
}