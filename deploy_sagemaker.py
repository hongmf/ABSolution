#!/usr/bin/env python3
"""
SageMaker Model Deployment Script
Trains and deploys ABS risk scoring model to AWS SageMaker
"""

import argparse
import boto3
import time
import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SageMakerDeployer:
    """Deploy models to AWS SageMaker"""

    def __init__(self, region='us-east-1', role_arn=None):
        """
        Initialize SageMaker deployer

        Args:
            region: AWS region
            role_arn: IAM role ARN for SageMaker (must have SageMaker execution permissions)
        """
        self.region = region
        self.role_arn = role_arn

        # Initialize AWS clients
        self.sagemaker = boto3.client('sagemaker', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.iam = boto3.client('iam', region_name=region)

        # Configuration
        self.bucket_name = None
        self.model_name = None
        self.endpoint_config_name = None
        self.endpoint_name = None

    def get_or_create_role(self):
        """
        Get existing SageMaker execution role or create one

        Returns:
            IAM role ARN
        """
        if self.role_arn:
            logger.info(f"Using provided role: {self.role_arn}")
            return self.role_arn

        role_name = 'ABSolutionSageMakerRole'

        try:
            # Try to get existing role
            role = self.iam.get_role(RoleName=role_name)
            role_arn = role['Role']['Arn']
            logger.info(f"Using existing role: {role_arn}")
            return role_arn
        except self.iam.exceptions.NoSuchEntityException:
            logger.info(f"Creating new SageMaker execution role: {role_name}")

            # Trust policy for SageMaker
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "sagemaker.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }

            # Create role
            role = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description='Execution role for ABSolution SageMaker models'
            )

            role_arn = role['Role']['Arn']

            # Attach managed policies
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess'
            )

            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
            )

            logger.info(f"Created role: {role_arn}")
            logger.info("Waiting 10 seconds for role to propagate...")
            time.sleep(10)

            return role_arn

    def create_s3_bucket(self, bucket_name=None):
        """
        Create S3 bucket for model artifacts

        Args:
            bucket_name: Name of bucket (auto-generated if not provided)

        Returns:
            Bucket name
        """
        if not bucket_name:
            account_id = boto3.client('sts').get_caller_identity()['Account']
            bucket_name = f"absolution-sagemaker-{account_id}-{self.region}"

        self.bucket_name = bucket_name

        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=bucket_name)
            logger.info(f"Using existing bucket: {bucket_name}")
        except:
            logger.info(f"Creating S3 bucket: {bucket_name}")

            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )

            logger.info(f"Created bucket: {bucket_name}")

        return bucket_name

    def train_local_model(self, output_dir='./model'):
        """
        Train model locally before uploading to SageMaker

        Args:
            output_dir: Directory to save trained model

        Returns:
            Path to model directory
        """
        logger.info("Training model locally...")

        # Import training module
        import sys
        sys.path.insert(0, 'src')
        from sagemaker.train_risk_model import train_model, argparse

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Prepare arguments
        args = argparse.Namespace(
            train_data=None,
            n_samples=10000,
            model_type='xgboost',
            model_dir=output_dir,
            output_data_dir=f'{output_dir}/output'
        )

        # Train model
        train_model(args)

        logger.info(f"Model trained and saved to: {output_dir}")
        return output_dir

    def upload_model_to_s3(self, model_dir, s3_prefix='models'):
        """
        Upload trained model to S3

        Args:
            model_dir: Local directory containing model artifacts
            s3_prefix: S3 prefix (folder) for model

        Returns:
            S3 URI of uploaded model
        """
        logger.info(f"Uploading model from {model_dir} to S3...")

        import tarfile

        # Create tarball
        tarball_path = '/tmp/model.tar.gz'
        with tarfile.open(tarball_path, 'w:gz') as tar:
            tar.add(model_dir, arcname='.')

        # Upload to S3
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        s3_key = f"{s3_prefix}/model-{timestamp}.tar.gz"

        self.s3.upload_file(tarball_path, self.bucket_name, s3_key)

        model_data_url = f"s3://{self.bucket_name}/{s3_key}"
        logger.info(f"Model uploaded to: {model_data_url}")

        return model_data_url

    def create_model(self, model_data_url, model_name=None):
        """
        Create SageMaker model

        Args:
            model_data_url: S3 URL of model artifacts
            model_name: Name for the model

        Returns:
            Model name
        """
        if not model_name:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            model_name = f"abs-risk-model-{timestamp}"

        self.model_name = model_name

        logger.info(f"Creating SageMaker model: {model_name}")

        # Get SageMaker scikit-learn container image
        from sagemaker import image_uris
        container = image_uris.retrieve(
            framework='sklearn',
            region=self.region,
            version='1.2-1',
            py_version='py3',
            image_scope='inference'
        )

        # Create model
        self.sagemaker.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': container,
                'ModelDataUrl': model_data_url,
                'Environment': {
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_SUBMIT_DIRECTORY': model_data_url
                }
            },
            ExecutionRoleArn=self.role_arn
        )

        logger.info(f"Model created: {model_name}")
        return model_name

    def create_endpoint_config(self, instance_type='ml.t2.medium', instance_count=1):
        """
        Create endpoint configuration

        Args:
            instance_type: EC2 instance type for endpoint
            instance_count: Number of instances

        Returns:
            Endpoint config name
        """
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        config_name = f"abs-risk-config-{timestamp}"
        self.endpoint_config_name = config_name

        logger.info(f"Creating endpoint configuration: {config_name}")

        self.sagemaker.create_endpoint_config(
            EndpointConfigName=config_name,
            ProductionVariants=[
                {
                    'VariantName': 'AllTraffic',
                    'ModelName': self.model_name,
                    'InstanceType': instance_type,
                    'InitialInstanceCount': instance_count,
                    'InitialVariantWeight': 1.0
                }
            ]
        )

        logger.info(f"Endpoint config created: {config_name}")
        return config_name

    def create_endpoint(self, endpoint_name=None):
        """
        Create and deploy endpoint

        Args:
            endpoint_name: Name for endpoint

        Returns:
            Endpoint name
        """
        if not endpoint_name:
            endpoint_name = 'abs-risk-endpoint'

        self.endpoint_name = endpoint_name

        # Check if endpoint exists
        try:
            response = self.sagemaker.describe_endpoint(EndpointName=endpoint_name)
            logger.info(f"Endpoint '{endpoint_name}' already exists with status: {response['EndpointStatus']}")

            if response['EndpointStatus'] == 'InService':
                logger.info("Updating existing endpoint...")
                self.sagemaker.update_endpoint(
                    EndpointName=endpoint_name,
                    EndpointConfigName=self.endpoint_config_name
                )
            else:
                logger.warning(f"Endpoint is in {response['EndpointStatus']} state. Please wait or delete it first.")
                return endpoint_name

        except self.sagemaker.exceptions.ClientError:
            # Endpoint doesn't exist, create new one
            logger.info(f"Creating new endpoint: {endpoint_name}")
            self.sagemaker.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=self.endpoint_config_name
            )

        # Wait for endpoint to be in service
        logger.info("Waiting for endpoint to be in service (this may take 5-10 minutes)...")

        waiter = self.sagemaker.get_waiter('endpoint_in_service')
        waiter.wait(EndpointName=endpoint_name)

        logger.info(f"✅ Endpoint '{endpoint_name}' is now in service!")
        return endpoint_name

    def deploy_full_stack(self, instance_type='ml.t2.medium', endpoint_name='abs-risk-endpoint'):
        """
        Complete end-to-end deployment

        Args:
            instance_type: Instance type for endpoint
            endpoint_name: Name for endpoint

        Returns:
            Deployment info dictionary
        """
        logger.info("=" * 60)
        logger.info("Starting Full SageMaker Deployment")
        logger.info("=" * 60)

        # Step 1: Get or create IAM role
        self.role_arn = self.get_or_create_role()

        # Step 2: Create S3 bucket
        bucket = self.create_s3_bucket()

        # Step 3: Train model locally
        model_dir = self.train_local_model()

        # Step 4: Upload to S3
        model_data_url = self.upload_model_to_s3(model_dir)

        # Step 5: Create SageMaker model
        model_name = self.create_model(model_data_url)

        # Step 6: Create endpoint config
        config_name = self.create_endpoint_config(instance_type=instance_type)

        # Step 7: Create and deploy endpoint
        endpoint = self.create_endpoint(endpoint_name=endpoint_name)

        # Summary
        info = {
            'endpoint_name': endpoint,
            'model_name': model_name,
            'endpoint_config': config_name,
            'bucket': bucket,
            'region': self.region,
            'role_arn': self.role_arn
        }

        logger.info("=" * 60)
        logger.info("✅ Deployment Complete!")
        logger.info("=" * 60)
        logger.info(f"Endpoint Name: {endpoint}")
        logger.info(f"Region: {self.region}")
        logger.info(f"S3 Bucket: {bucket}")
        logger.info("=" * 60)
        logger.info("\nAdd this to your .env file:")
        logger.info(f"SAGEMAKER_ENDPOINT_NAME={endpoint}")
        logger.info(f"AWS_REGION={self.region}")
        logger.info("=" * 60)

        return info


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Deploy SageMaker model for ABSolution')

    parser.add_argument('--region', type=str, default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--role-arn', type=str, default=None,
                       help='IAM role ARN for SageMaker (will create if not provided)')
    parser.add_argument('--instance-type', type=str, default='ml.t2.medium',
                       help='Instance type for endpoint (default: ml.t2.medium)')
    parser.add_argument('--endpoint-name', type=str, default='abs-risk-endpoint',
                       help='Name for the endpoint (default: abs-risk-endpoint)')

    args = parser.parse_args()

    # Create deployer and run full deployment
    deployer = SageMakerDeployer(region=args.region, role_arn=args.role_arn)

    try:
        info = deployer.deploy_full_stack(
            instance_type=args.instance_type,
            endpoint_name=args.endpoint_name
        )

        # Save deployment info
        with open('sagemaker_deployment_info.json', 'w') as f:
            json.dump(info, f, indent=2)

        logger.info("\nDeployment info saved to: sagemaker_deployment_info.json")

    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise


if __name__ == '__main__':
    main()
