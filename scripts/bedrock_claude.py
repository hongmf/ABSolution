import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def call_bedrock_claude(prompt, data_summary):
    """Call Claude via AWS Bedrock"""
    bedrock = boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('BEDROCK_REGION', 'us-west-2'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": f"{prompt}\n\nAnalyze this data and recommend visualizations:\n{data_summary}"
        }]
    })
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return result['content'][0]['text']