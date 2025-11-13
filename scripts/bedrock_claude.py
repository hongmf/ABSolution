import boto3
import json

def call_bedrock_claude(prompt, data_summary, region='us-east-1'):
    """Call Claude via AWS Bedrock"""
    bedrock = boto3.client('bedrock-runtime', region_name=region)
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": f"{prompt}\n\nAnalyze this data and recommend visualizations:\n{data_summary}"
        }]
    })
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return result['content'][0]['text']

# Usage:
# recommendations = call_bedrock_claude(viz_prompt, data_summary)