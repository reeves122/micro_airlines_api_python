
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
  role = aws_iam_role.micro_airlines_api_lambda_role.id

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
