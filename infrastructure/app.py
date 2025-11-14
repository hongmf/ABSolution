#!/usr/bin/env python3
"""
ABSolution CDK Application
AWS Infrastructure as Code for Multi-Agent System
"""

import os
import aws_cdk as cdk
from multi_agent_stack import MultiAgentStack


app = cdk.App()

# Get environment configuration
account = os.environ.get('CDK_DEFAULT_ACCOUNT')
region = os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')

# Create the stack
MultiAgentStack(
    app,
    "ABSolutionMultiAgentStack",
    env=cdk.Environment(
        account=account,
        region=region
    ),
    description="ABSolution Multi-Agent AI System Infrastructure"
)

# Add tags to all resources
cdk.Tags.of(app).add("Project", "ABSolution")
cdk.Tags.of(app).add("Environment", "Production")
cdk.Tags.of(app).add("ManagedBy", "CDK")

app.synth()
