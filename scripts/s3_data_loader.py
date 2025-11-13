import boto3
import pandas as pd
import os
from dotenv import load_dotenv
import io

load_dotenv()

def list_s3_folders():
    """List folders in S3 bucket"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    bucket = os.getenv('S3_BUCKET_NAME')
    response = s3.list_objects_v2(Bucket=bucket, Delimiter='/')
    
    folders = []
    if 'CommonPrefixes' in response:
        folders = [prefix['Prefix'].rstrip('/') for prefix in response['CommonPrefixes']]
    
    return folders

def list_s3_files(folder):
    """List all files in S3 folder"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    bucket = os.getenv('S3_BUCKET_NAME')
    response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{folder}/")
    
    files = []
    if 'Contents' in response:
        files = [obj['Key'] for obj in response['Contents'] 
                if not obj['Key'].endswith('/')]  # Exclude folders
    
    return files

def load_s3_file(file_key):
    """Load file from S3 - supports CSV, TXT, JSON, XML, and other formats"""
    import json
    import xml.etree.ElementTree as ET
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    bucket = os.getenv('S3_BUCKET_NAME')
    obj = s3.get_object(Bucket=bucket, Key=file_key)
    content = obj['Body'].read()
    
    if file_key.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
    elif file_key.endswith('.txt'):
        # Try different separators for txt files
        text_content = content.decode('utf-8')
        try:
            df = pd.read_csv(io.StringIO(text_content), sep='\t')
        except:
            try:
                df = pd.read_csv(io.StringIO(text_content), sep=',')
            except:
                df = pd.read_csv(io.StringIO(text_content), sep='|')
    elif file_key.endswith('.json'):
        # Handle JSON files
        json_content = json.loads(content.decode('utf-8'))
        if isinstance(json_content, list):
            df = pd.DataFrame(json_content)
        elif isinstance(json_content, dict):
            df = pd.json_normalize(json_content)
        else:
            df = pd.DataFrame([json_content])
    elif file_key.endswith('.xml'):
        # Handle XML files
        root = ET.fromstring(content.decode('utf-8'))
        data = []
        for child in root:
            row = {}
            for subchild in child:
                row[subchild.tag] = subchild.text
            data.append(row)
        df = pd.DataFrame(data)
    else:
        # For other file types, try to read as CSV
        try:
            df = pd.read_csv(io.BytesIO(content))
        except:
            raise ValueError(f"Cannot read file format: {file_key}")
    
    return df