resource "aws_dynamodb_table" "players_table" {
  name           = "${var.name}-players-${var.env}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "player_id"

  attribute {
    name = "player_id"
    type = "S"
  }
}
