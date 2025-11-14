"""
Dialogue Panel Handler for ABSolution Multi-Agent System
Provides a conversational interface for users to interact with AI agents
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import boto3

from agent_coordinator import AgentCoordinator


class DialoguePanel:
    """
    Manages user conversations with the multi-agent system.
    Provides context management, session handling, and response formatting.
    """

    def __init__(self):
        self.coordinator = AgentCoordinator()
        self.dynamodb = boto3.resource('dynamodb')
        self.session_table = self.dynamodb.Table('abs-agent-sessions')

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        self.session_table.put_item(
            Item={
                'session_id': session_id,
                'user_id': user_id or 'anonymous',
                'created_at': timestamp,
                'last_activity': timestamp,
                'status': 'active',
                'context': {}
            }
        )

        return session_id

    def process_message(
        self,
        session_id: str,
        user_message: str,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the multi-agent system.
        """
        # Load session context
        session = self._load_session(session_id)

        if not session:
            return {
                'error': 'Invalid session',
                'message': 'Please create a new session'
            }

        # Build context from session and attachments
        context = session.get('context', {})

        if attachments:
            context['attachments'] = attachments

        # Process through coordinator
        result = self.coordinator.orchestrate_multi_agent(
            user_query=user_message,
            session_id=session_id,
            context=context
        )

        # Update session context with any new information
        self._update_session_context(session_id, result)

        # Format response for dialogue panel
        response = self._format_response(result)

        return response

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a session."""
        history = self.coordinator._load_conversation(session_id)
        return history[-limit:] if history else []

    def add_context(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Add contextual information to the session."""
        try:
            session = self._load_session(session_id)
            if not session:
                return False

            context = session.get('context', {})
            context[key] = value

            self.session_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET context = :ctx, last_activity = :ts',
                ExpressionAttributeValues={
                    ':ctx': context,
                    ':ts': datetime.utcnow().isoformat()
                }
            )
            return True

        except Exception as e:
            print(f"Error adding context: {str(e)}")
            return False

    def suggest_follow_ups(
        self,
        session_id: str,
        last_response: str
    ) -> List[str]:
        """Generate suggested follow-up questions based on the conversation."""
        # Use Bedrock to generate contextual suggestions
        prompt = f"""Based on this ABS analysis response, suggest 3 relevant follow-up questions a user might ask.
Make them specific and actionable.

Response: {last_response[:500]}...

Suggested questions (numbered list):"""

        suggestions = self.coordinator._invoke_bedrock(
            model_id="anthropic.claude-v2",
            prompt=prompt,
            max_tokens=200,
            temperature=0.8
        )

        # Parse suggestions
        lines = suggestions.strip().split('\n')
        return [line.strip('123456789. ') for line in lines if line.strip()][:3]

    def export_conversation(
        self,
        session_id: str,
        format: str = 'json'
    ) -> str:
        """Export conversation history in various formats."""
        history = self.get_conversation_history(session_id, limit=1000)

        if format == 'json':
            return json.dumps(history, indent=2)

        elif format == 'markdown':
            md = f"# Conversation Export\n\n**Session ID:** {session_id}\n\n"
            for turn in history:
                md += f"## {turn['timestamp']}\n\n"
                md += f"**User:** {turn['user']}\n\n"
                md += f"**Assistant:** {turn['assistant']}\n\n"
                md += "---\n\n"
            return md

        elif format == 'text':
            txt = ""
            for turn in history:
                txt += f"[{turn['timestamp']}]\n"
                txt += f"User: {turn['user']}\n"
                txt += f"Assistant: {turn['assistant']}\n\n"
            return txt

        return ""

    def _load_session(self, session_id: str) -> Optional[Dict]:
        """Load session data from DynamoDB."""
        try:
            response = self.session_table.get_item(
                Key={'session_id': session_id}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error loading session: {str(e)}")
            return None

    def _update_session_context(
        self,
        session_id: str,
        agent_result: Dict[str, Any]
    ) -> None:
        """Extract and save relevant context from agent responses."""
        try:
            # Extract entities mentioned (security IDs, dates, etc.)
            context_updates = {}

            # Check if any security IDs were mentioned
            for response_data in agent_result.get('agent_responses', []):
                response_text = response_data.get('response', '')

                # Simple extraction (in production, use NER)
                if 'security' in response_text.lower():
                    context_updates['last_security_discussed'] = True

            # Update session
            self.session_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET last_activity = :ts',
                ExpressionAttributeValues={
                    ':ts': datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            print(f"Error updating session context: {str(e)}")

    def _format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format agent coordination result for dialogue panel display."""
        return {
            'message': result['final_response'],
            'metadata': {
                'agents_consulted': [
                    r['agent'] for r in result['agent_responses']
                ],
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': result['session_id']
            },
            'suggestions': [],  # Will be populated by suggest_follow_ups
            'visualization_hints': self._extract_visualization_hints(result)
        }

    def _extract_visualization_hints(
        self,
        result: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Suggest visualizations based on the response content.
        """
        hints = []
        final_response = result.get('final_response', '').lower()

        if any(word in final_response for word in ['trend', 'over time', 'history']):
            hints.append({
                'type': 'line_chart',
                'description': 'Time series visualization recommended'
            })

        if any(word in final_response for word in ['compare', 'vs', 'versus', 'benchmark']):
            hints.append({
                'type': 'bar_chart',
                'description': 'Comparative bar chart recommended'
            })

        if any(word in final_response for word in ['risk score', 'rating', 'metric']):
            hints.append({
                'type': 'gauge',
                'description': 'Risk score gauge recommended'
            })

        if any(word in final_response for word in ['composition', 'breakdown', 'distribution']):
            hints.append({
                'type': 'pie_chart',
                'description': 'Distribution chart recommended'
            })

        return hints


# Lambda handler for WebSocket API (real-time dialogue)
def websocket_handler(event, context):
    """
    Handle WebSocket connections for real-time dialogue.
    """
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')

    dialogue = DialoguePanel()

    if route_key == '$connect':
        # New connection - create session
        session_id = dialogue.create_session()
        return {
            'statusCode': 200,
            'body': json.dumps({'session_id': session_id})
        }

    elif route_key == '$disconnect':
        # Connection closed
        return {'statusCode': 200}

    elif route_key == 'message':
        # Process user message
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('session_id')
        message = body.get('message')

        if not session_id or not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing session_id or message'})
            }

        # Process message
        response = dialogue.process_message(session_id, message)

        # Get follow-up suggestions
        suggestions = dialogue.suggest_follow_ups(session_id, response['message'])
        response['suggestions'] = suggestions

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }

    return {'statusCode': 400, 'body': 'Invalid route'}


# Lambda handler for REST API
def rest_api_handler(event, context):
    """
    Handle REST API requests for dialogue panel.
    """
    http_method = event.get('httpMethod')
    path = event.get('path')
    body = json.loads(event.get('body', '{}'))

    dialogue = DialoguePanel()

    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    if http_method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}

    # POST /session - Create new session
    if http_method == 'POST' and path == '/session':
        session_id = dialogue.create_session(body.get('user_id'))
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'session_id': session_id})
        }

    # POST /message - Send message
    elif http_method == 'POST' and path == '/message':
        session_id = body.get('session_id')
        message = body.get('message')
        attachments = body.get('attachments')

        if not session_id or not message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        response = dialogue.process_message(session_id, message, attachments)
        suggestions = dialogue.suggest_follow_ups(session_id, response['message'])
        response['suggestions'] = suggestions

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response)
        }

    # GET /history/{session_id} - Get conversation history
    elif http_method == 'GET' and '/history/' in path:
        session_id = path.split('/')[-1]
        history = dialogue.get_conversation_history(session_id)

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'history': history})
        }

    # POST /export - Export conversation
    elif http_method == 'POST' and path == '/export':
        session_id = body.get('session_id')
        format = body.get('format', 'json')

        export_data = dialogue.export_conversation(session_id, format)

        return {
            'statusCode': 200,
            'headers': {
                **headers,
                'Content-Type': f'text/{format}' if format != 'json' else 'application/json'
            },
            'body': export_data
        }

    return {
        'statusCode': 404,
        'headers': headers,
        'body': json.dumps({'error': 'Not found'})
    }
