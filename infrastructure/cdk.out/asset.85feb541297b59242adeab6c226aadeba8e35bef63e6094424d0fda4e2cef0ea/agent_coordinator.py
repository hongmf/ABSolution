"""
Multi-Agent Coordinator for ABSolution
Orchestrates multiple specialized AI agents using AWS services
"""

import json
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# Import all agent prompts
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from prompt import (
    data_analyst_prompt,
    risk_assessor_prompt,
    report_generator_prompt,
    benchmark_analyst_prompt,
    alert_monitor_prompt
)


class AgentCoordinator:
    """
    Coordinates multiple AI agents to work together on complex ABS analysis tasks.
    Uses AWS Bedrock for agent LLM capabilities and Step Functions for orchestration.
    """

    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.dynamodb = boto3.resource('dynamodb')
        self.stepfunctions = boto3.client('stepfunctions')
        self.sagemaker_runtime = boto3.client('sagemaker-runtime')

        # Agent registry
        self.agents = {
            'data_analyst': data_analyst_prompt,
            'risk_assessor': risk_assessor_prompt,
            'report_generator': report_generator_prompt,
            'benchmark_analyst': benchmark_analyst_prompt,
            'alert_monitor': alert_monitor_prompt
        }

        # Conversation state table
        self.conversation_table = self.dynamodb.Table(
            os.environ.get('CONVERSATION_TABLE', 'abs-agent-conversations')
        )

    def route_query(self, user_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently route user query to appropriate agent(s).
        Uses intent classification to determine which agents to invoke.
        """
        # Classify intent using Bedrock
        intent = self._classify_intent(user_query)

        routing_plan = {
            'primary_agent': None,
            'supporting_agents': [],
            'execution_strategy': 'sequential'  # or 'parallel'
        }

        # Intent-based routing logic
        if 'data' in intent or 'query' in intent or 'show' in intent:
            routing_plan['primary_agent'] = 'data_analyst'

        elif 'risk' in intent or 'assess' in intent or 'score' in intent:
            routing_plan['primary_agent'] = 'risk_assessor'
            routing_plan['supporting_agents'] = ['data_analyst']

        elif 'report' in intent or 'summary' in intent or 'write' in intent:
            routing_plan['primary_agent'] = 'report_generator'
            routing_plan['supporting_agents'] = ['data_analyst', 'risk_assessor']

        elif 'compare' in intent or 'benchmark' in intent or 'performance' in intent:
            routing_plan['primary_agent'] = 'benchmark_analyst'
            routing_plan['supporting_agents'] = ['data_analyst']

        elif 'alert' in intent or 'monitor' in intent or 'watch' in intent:
            routing_plan['primary_agent'] = 'alert_monitor'

        else:
            # Default: use data analyst for exploration
            routing_plan['primary_agent'] = 'data_analyst'

        return routing_plan

    def _classify_intent(self, query: str) -> List[str]:
        """Use Bedrock to classify user intent."""
        prompt = f"""Analyze this user query and identify the primary intents.
Return only keywords like: data, query, risk, assess, report, summary, compare, benchmark, alert, monitor.

Query: {query}

Intents:"""

        response = self._invoke_bedrock(
            model_id="anthropic.claude-v2",
            prompt=prompt,
            max_tokens=50,
            temperature=0.1
        )

        return response.lower().split()

    def execute_agent(
        self,
        agent_name: str,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific agent with given task and context.
        """
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent_prompt = self.agents[agent_name]

        # Build the full prompt
        system_prompt = agent_prompt.SYSTEM_PROMPT
        user_prompt = agent_prompt.USER_PROMPT_TEMPLATE.format(
            task=task,
            **context
        )

        # Get agent configuration
        config = agent_prompt.AGENT_CONFIG

        # Invoke Bedrock
        response = self._invoke_bedrock(
            model_id=agent_prompt.MODEL_ID,
            system_prompt=system_prompt,
            prompt=user_prompt,
            **config
        )

        # For risk assessor, also invoke SageMaker if needed
        if agent_name == 'risk_assessor' and 'security_id' in context:
            ml_score = self._invoke_sagemaker_risk_model(context['security_id'])
            response = f"{response}\n\nML Risk Score: {ml_score}"

        return {
            'agent': agent_name,
            'response': response,
            'timestamp': datetime.utcnow().isoformat(),
            'context': context
        }

    def orchestrate_multi_agent(
        self,
        user_query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method - coordinates multiple agents to answer complex queries.
        """
        if context is None:
            context = {}

        # Load conversation history
        conversation_history = self._load_conversation(session_id)

        # Route the query
        routing_plan = self.route_query(user_query, context)

        results = {
            'session_id': session_id,
            'query': user_query,
            'routing_plan': routing_plan,
            'agent_responses': [],
            'final_response': None
        }

        # Execute supporting agents first (if any)
        for agent_name in routing_plan['supporting_agents']:
            try:
                agent_result = self.execute_agent(
                    agent_name=agent_name,
                    task=user_query,
                    context=context
                )
                results['agent_responses'].append(agent_result)

                # Add agent results to context for next agents
                context[f'{agent_name}_output'] = agent_result['response']

            except Exception as e:
                print(f"Error executing {agent_name}: {str(e)}")
                results['agent_responses'].append({
                    'agent': agent_name,
                    'error': str(e)
                })

        # Execute primary agent
        primary_agent = routing_plan['primary_agent']
        try:
            primary_result = self.execute_agent(
                agent_name=primary_agent,
                task=user_query,
                context=context
            )
            results['agent_responses'].append(primary_result)
            results['final_response'] = primary_result['response']

        except Exception as e:
            print(f"Error executing primary agent {primary_agent}: {str(e)}")
            results['final_response'] = f"Error: {str(e)}"

        # Save conversation state
        self._save_conversation(session_id, user_query, results['final_response'])

        return results

    def _invoke_bedrock(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """Invoke Amazon Bedrock model."""

        # Build request body based on model
        if 'anthropic' in model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            if system_prompt:
                body["system"] = system_prompt

        else:  # Amazon Titan or other models
            body = {
                "inputText": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }

        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )

            response_body = json.loads(response['body'].read())

            # Extract text based on model
            if 'anthropic' in model_id:
                return response_body['content'][0]['text']
            else:
                return response_body['results'][0]['outputText']

        except Exception as e:
            print(f"Bedrock invocation error: {str(e)}")
            raise

    def _invoke_sagemaker_risk_model(self, security_id: str) -> float:
        """Invoke SageMaker risk scoring model."""
        endpoint_name = os.environ.get(
            'SAGEMAKER_RISK_ENDPOINT',
            'abs-risk-scoring-model'
        )

        try:
            # Prepare input data (simplified - would need actual feature engineering)
            payload = json.dumps({
                'security_id': security_id
            })

            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='application/json',
                Body=payload
            )

            result = json.loads(response['Body'].read())
            return result.get('risk_score', 0.0)

        except Exception as e:
            print(f"SageMaker invocation error: {str(e)}")
            return 0.0

    def _load_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """Load conversation history from DynamoDB."""
        try:
            response = self.conversation_table.get_item(
                Key={'session_id': session_id}
            )
            return response.get('Item', {}).get('history', [])
        except Exception as e:
            print(f"Error loading conversation: {str(e)}")
            return []

    def _save_conversation(
        self,
        session_id: str,
        user_query: str,
        agent_response: str
    ) -> None:
        """Save conversation turn to DynamoDB."""
        try:
            timestamp = datetime.utcnow().isoformat()

            # Load existing history
            history = self._load_conversation(session_id)

            # Append new turn
            history.append({
                'timestamp': timestamp,
                'user': user_query,
                'assistant': agent_response
            })

            # Keep only last 50 turns
            history = history[-50:]

            # Save back
            self.conversation_table.put_item(
                Item={
                    'session_id': session_id,
                    'history': history,
                    'last_updated': timestamp
                }
            )
        except Exception as e:
            print(f"Error saving conversation: {str(e)}")


# Lambda handler for API Gateway integration
def lambda_handler(event, context):
    """
    AWS Lambda handler for dialogue panel API.
    """
    coordinator = AgentCoordinator()

    # Parse request
    body = json.loads(event.get('body', '{}'))
    user_query = body.get('query', '')
    session_id = body.get('session_id', 'default')
    context_data = body.get('context', {})

    # Orchestrate agents
    result = coordinator.orchestrate_multi_agent(
        user_query=user_query,
        session_id=session_id,
        context=context_data
    )

    # Return response
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'response': result['final_response'],
            'session_id': session_id,
            'agents_used': [r['agent'] for r in result['agent_responses']],
            'timestamp': datetime.utcnow().isoformat()
        })
    }
