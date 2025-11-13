import boto3
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def load_dynamodb_table(table_name='AutoLoanMetrics'):
    """Load data from DynamoDB table"""
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    table = dynamodb.Table(table_name)
    response = table.scan()
    
    items = response['Items']
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    
    # Convert to DataFrame
    df = pd.DataFrame(items)
    
    return df

def list_dynamodb_tables():
    """List all DynamoDB tables"""
    dynamodb = boto3.client(
        'dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    response = dynamodb.list_tables()
    return response['TableNames']