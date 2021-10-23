resource "aws_dynamodb_table" "players" {
  name         = "${local.name}_players"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "player_id"

  attribute {
    name = "player_id"
    type = "S"
  }
}
