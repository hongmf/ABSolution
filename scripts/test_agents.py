#!/usr/bin/env python3
"""
Test script for ABSolution Multi-Agent System
Tests each agent and the coordination system
"""

import json
import requests
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents import AgentCoordinator, DialoguePanel


def test_local_agents():
    """Test agents locally without AWS deployment."""
    print("=" * 60)
    print("Testing ABSolution Multi-Agent System Locally")
    print("=" * 60)
    print()

    # Mock AWS environment for local testing
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['CONVERSATION_TABLE'] = 'abs-agent-conversations'
    os.environ['SESSION_TABLE'] = 'abs-agent-sessions'

    print("Note: This requires AWS credentials and Bedrock access")
    print()

    try:
        coordinator = AgentCoordinator()
        print("✓ Agent Coordinator initialized")

        # Test intent classification
        print("\n1. Testing Intent Classification...")
        print("-" * 40)

        test_queries = [
            "Show me all auto ABS deals from Q1 2024",
            "What's the risk score for security ABC-123?",
            "Generate a deal analysis report",
            "Compare this deal to market average",
            "Alert me if defaults spike"
        ]

        for query in test_queries:
            intent = coordinator._classify_intent(query)
            routing = coordinator.route_query(query, {})
            print(f"\nQuery: {query}")
            print(f"Intent: {intent}")
            print(f"Primary Agent: {routing['primary_agent']}")
            print(f"Supporting Agents: {routing['supporting_agents']}")

        # Test individual agent (with mock context)
        print("\n2. Testing Individual Agent Execution...")
        print("-" * 40)

        test_context = {
            "security_id": "ABC-123",
            "data_sources": ["S3", "Athena"],
            "context": "Test security analysis"
        }

        result = coordinator.execute_agent(
            agent_name="data_analyst",
            task="Analyze security ABC-123",
            context=test_context
        )

        print(f"\nAgent: {result['agent']}")
        print(f"Response: {result['response'][:200]}...")
        print(f"Timestamp: {result['timestamp']}")

        print("\n✓ All local tests passed!")

    except Exception as e:
        print(f"\n✗ Error during testing: {str(e)}")
        print("\nNote: Some tests require AWS credentials and Bedrock access")
        return False

    return True


def test_deployed_api(api_endpoint):
    """Test deployed API endpoints."""
    print("\n" + "=" * 60)
    print("Testing Deployed API")
    print("=" * 60)
    print()

    print(f"API Endpoint: {api_endpoint}")
    print()

    try:
        # Test 1: Create session
        print("1. Creating session...")
        response = requests.post(
            f"{api_endpoint}/session",
            json={"user_id": "test_user"}
        )
        response.raise_for_status()
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✓ Session created: {session_id}")

        # Test 2: Send message
        print("\n2. Sending test message...")
        response = requests.post(
            f"{api_endpoint}/message",
            json={
                "session_id": session_id,
                "message": "What are the key metrics for ABS analysis?"
            }
        )
        response.raise_for_status()
        message_data = response.json()
        print(f"✓ Response received")
        print(f"  Message: {message_data['message'][:200]}...")
        print(f"  Agents used: {message_data['metadata']['agents_consulted']}")
        print(f"  Suggestions: {message_data.get('suggestions', [])}")

        # Test 3: Get history
        print("\n3. Retrieving conversation history...")
        response = requests.get(f"{api_endpoint}/history/{session_id}")
        response.raise_for_status()
        history_data = response.json()
        print(f"✓ History retrieved: {len(history_data['history'])} turns")

        # Test 4: Export conversation
        print("\n4. Exporting conversation...")
        response = requests.post(
            f"{api_endpoint}/export",
            json={
                "session_id": session_id,
                "format": "json"
            }
        )
        response.raise_for_status()
        print("✓ Conversation exported successfully")

        print("\n✓ All API tests passed!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n✗ API test failed: {str(e)}")
        return False


def main():
    """Main test runner."""
    print()
    print("ABSolution Multi-Agent System - Test Suite")
    print()

    # Check if API endpoint provided
    if len(sys.argv) > 1:
        api_endpoint = sys.argv[1]
        print(f"Testing deployed API at: {api_endpoint}")
        success = test_deployed_api(api_endpoint)
    else:
        print("No API endpoint provided. Running local tests...")
        print("(To test deployed API, run: python test_agents.py https://your-api-endpoint)")
        print()
        success = test_local_agents()

    print()
    if success:
        print("=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("✗ Some tests failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
