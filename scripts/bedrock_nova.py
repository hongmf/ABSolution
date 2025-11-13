import boto3
import json

def call_bedrock_nova(prompt, data_summary, region='us-east-1'):
    """Call Nova Lite via AWS Bedrock"""
    bedrock = boto3.client('bedrock-runtime', region_name=region)
    
    body = json.dumps({
        "messages": [{
            "role": "user",
            "content": [{
                "text": f"{prompt}\n\nAnalyze this data and recommend visualizations:\n{data_summary}"
            }]
        }],
        "inferenceConfig": {
            "maxTokens": 1000,
            "temperature": 0.7
        }
    })
    
    response = bedrock.invoke_model(
        modelId='amazon.nova-lite-v1:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return result['output']['message']['content'][0]['text']

# Usage:
# recommendations = call_bedrock_nova(viz_prompt, data_summary)