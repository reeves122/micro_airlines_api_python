import boto3


def create_table():
    """
    Create dynamodb table
    """
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='players',
        AttributeDefinitions=[
            {
                'AttributeName': 'player_id',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                'AttributeName': 'player_id',
                'KeyType': 'HASH'
            }
        ]
    )
