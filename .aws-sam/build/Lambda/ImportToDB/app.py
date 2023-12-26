import json
import boto3
import re
import os

def lambda_handler(event, context):
    # data = json.loads(event['body'])
    tableName = os.environ('TableName')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(tableName)
    response = table.put_item(
        Item={
            'FaceID': event['FaceID'],
            'Name': event['Name'],
            'BucketLocation': event['BucketLocation'],
            'BoundingBox': event['BoundingBox']
        }
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        # Return JSON
        return json.dumps(response)