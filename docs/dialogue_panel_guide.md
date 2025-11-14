# ABSolution Dialogue Panel User Guide

## Overview

The ABSolution Dialogue Panel is a modern web interface for interacting with the multi-agent AI system. It provides an intuitive chat interface where you can query ABS data, assess risks, generate reports, and more.

## Interface Components

### 1. Header Bar

Located at the top of the screen:

- **Logo & Title**: ABSolution branding
- **Connection Status**: Shows real-time connection state
  - 🟢 Green dot = Connected
  - 🟡 Yellow dot = Connecting
  - 🔴 Red dot = Disconnected
- **Session ID**: Your unique conversation session identifier

### 2. Agent Sidebar (Left)

Displays all 5 specialized AI agents:

#### 📊 Data Analyst
- **Purpose**: Query and analyze SEC filings data
- **Use when**: You need data, metrics, or historical information
- **Example**: "Show me all auto ABS deals from Q1 2024"

#### ⚠️ Risk Assessor
- **Purpose**: Evaluate credit risk and generate risk scores
- **Use when**: Assessing security risk, evaluating collateral quality
- **Example**: "What's the risk score for security ABC-123?"

#### 📝 Report Generator
- **Purpose**: Create narrative reports and recommendations
- **Use when**: You need formatted reports or summaries
- **Example**: "Generate a deal analysis report for XYZ security"

#### 📈 Benchmark Analyst
- **Purpose**: Compare performance against benchmarks
- **Use when**: Comparing securities or analyzing relative performance
- **Example**: "Compare this deal to similar vintage"

#### 🔔 Alert Monitor
- **Purpose**: Detect anomalies and generate alerts
- **Use when**: Monitoring for unusual activity or threshold breaches
- **Example**: "Alert me if default rates spike above 5%"

**Agent Status Indicators**:
- Gray dot: Inactive
- Green pulsing dot: Currently processing your query
- Cards highlight when active

### 3. Chat Area (Center)

#### Welcome Message
When you first open the panel, you'll see a welcome message with:
- System overview
- List of capabilities
- Example queries you can try

#### Message Types

**Your Messages** (Blue, right-aligned):
- Questions and commands you send
- Displayed on the right side
- Blue background

**AI Responses** (Gray, left-aligned):
- Answers from the multi-agent system
- Displayed on the left side
- Gray background with border
- Includes metadata showing which agents were consulted

**System Messages** (Purple gradient, full-width):
- System notifications
- Error messages
- Status updates

#### Message Features

- **Agent Attribution**: See which agents contributed to each response
- **Timestamps**: When each message was sent
- **Markdown Support**: Formatted text with bold, italic, lists, and code
- **Auto-scroll**: Automatically scrolls to show latest messages

#### Typing Indicator

When agents are processing your query, you'll see:
- Three animated dots
- Text: "Agents are analyzing..."

### 4. Suggestions Bar

After receiving a response, the system may suggest relevant follow-up questions:
- Displayed as clickable chips
- Click any suggestion to automatically send it
- AI-generated based on conversation context

### 5. Input Area (Bottom)

#### Text Input
- **Placeholder**: "Ask me anything about Asset-Backed Securities..."
- **Auto-resize**: Grows as you type (max 150px height)
- **Character limit**: 2000 characters
- **Character counter**: Shows "X/2000" in bottom right

#### Send Button
- Blue circular button with send icon
- Click to send message
- Disabled while processing
- Keyboard shortcut: **Ctrl+Enter**

#### Quick Actions Sidebar

Pre-built queries for common tasks:

- **Recent Deals**: Query recent ABS issuances
- **Market Summary**: Get current market overview
- **High Risk Alerts**: View securities needing attention
- **Clear Chat**: Reset conversation (asks for confirmation)
- **Export Chat**: Download conversation as Markdown file

## Getting Started

### First Time Setup

1. **Open the Dialogue Panel**
   ```bash
   # Option 1: Using Python
   python3 scripts/serve_ui.py

   # Option 2: Simple HTTP server
   cd src/frontend
   python3 -m http.server 8080
   ```

2. **Configure API Endpoint**
   - On first launch, you'll see a configuration modal
   - Enter your API Gateway endpoint
   - Format: `https://your-api-id.execute-api.region.amazonaws.com/prod`
   - Optionally enter API key if required
   - Click "Save"

3. **Session Created**
   - The system automatically creates a session
   - You'll see "Connected" status in the header
   - Session ID displayed (e.g., "Session: abc12345...")

### Sending Your First Query

1. **Type your question** in the input box
   ```
   "Show me all auto ABS deals from Q1 2024"
   ```

2. **Press Send** (click button or Ctrl+Enter)

3. **Watch the agents work**
   - Agent cards highlight in the sidebar
   - Typing indicator appears
   - Multiple agents may activate for complex queries

4. **Review the response**
   - Response appears on the left
   - Agent badges show which agents were used
   - Timestamp shown

5. **Follow up**
   - Use suggested questions (if shown)
   - Or type your own follow-up question

## Usage Examples

### Example 1: Data Query

**Query**:
```
"Show me all auto ABS deals from Q1 2024"
```

**What happens**:
1. System routes to **Data Analyst** agent
2. Agent queries SEC filings database
3. Returns list of deals with key metrics

**Expected response**:
- List of securities
- Issuance dates
- Principal amounts
- Key metrics

### Example 2: Risk Assessment

**Query**:
```
"What's the risk score for security ABC-123?"
```

**What happens**:
1. System routes to **Risk Assessor** (primary) and **Data Analyst** (supporting)
2. Data Analyst fetches security data
3. Risk Assessor calculates score using ML model
4. Returns comprehensive risk assessment

**Expected response**:
- Risk score (0-100)
- Risk category (Low/Medium/High/Critical)
- Key risk factors
- Recommendations

### Example 3: Comprehensive Report

**Query**:
```
"Generate a deal analysis report for security ABC-123"
```

**What happens**:
1. System executes agents in parallel:
   - Data Analyst: Fetches deal data
   - Risk Assessor: Calculates risk score
   - Benchmark Analyst: Compares to peers
2. Report Generator compiles all information
3. Returns formatted report

**Expected response**:
- Executive summary
- Deal structure details
- Risk analysis
- Benchmark comparison
- Recommendations

### Example 4: Comparative Analysis

**Query**:
```
"Compare security ABC-123 to similar vintage deals"
```

**What happens**:
1. **Benchmark Analyst** (primary) with **Data Analyst** (supporting)
2. Identifies peer group
3. Compares key metrics
4. Highlights differences

**Expected response**:
- Peer group definition
- Comparative metrics table
- Performance ranking
- Key differentiators

### Example 5: Alert Setup

**Query**:
```
"Alert me if default rates for security ABC-123 spike above 5%"
```

**What happens**:
1. **Alert Monitor** agent processes request
2. Sets up monitoring rule in EventBridge
3. Configures threshold
4. Confirms alert created

**Expected response**:
- Confirmation of alert setup
- Monitoring parameters
- Expected behavior
- How to manage alerts

## Advanced Features

### Conversation Context

The system maintains context across messages:

```
You: "Show me security ABC-123"
AI: [Returns security details]

You: "What's the risk score?"
AI: [Knows you're asking about ABC-123]

You: "Compare it to peers"
AI: [Still knows the context]
```

### Multi-Agent Coordination

Complex queries automatically trigger multiple agents:

**Query**: "Assess risk and generate report for ABC-123"

**System behavior**:
- Recognizes multiple intents (assess + report)
- Executes agents in sequence or parallel
- Coordinates results
- Returns comprehensive answer

### Follow-up Suggestions

AI generates contextual suggestions:

**After data query**:
- "What's the risk assessment?"
- "Compare to benchmarks"
- "Show historical performance"

**After risk assessment**:
- "Generate detailed report"
- "What are mitigation strategies?"
- "Show similar high-risk securities"

### Export Conversations

Save your conversation for later reference:

1. Click "Export Chat" in sidebar
2. File downloads as Markdown
3. Filename: `abs-conversation-[timestamp].md`
4. Includes full conversation with timestamps

## Keyboard Shortcuts

- **Ctrl+Enter**: Send message
- **Escape**: Clear input (without sending)

## Tips & Best Practices

### 1. Be Specific

❌ Bad: "Tell me about ABS"
✅ Good: "Show me auto ABS deals issued in Q1 2024 with AAA rating"

### 2. Use Context

The system remembers your conversation:
```
"Show me security ABC-123"
"What's its risk score?"  // No need to repeat "ABC-123"
"Compare to market average"  // Still knows the context
```

### 3. Ask Follow-ups

Use suggestions or ask related questions:
```
Initial: "What's the risk score?"
Follow-up: "What are the main risk factors?"
Follow-up: "How does this compare to last quarter?"
```

### 4. Request Specific Formats

```
"Generate a brief summary of security ABC-123"
"Create a detailed report with all metrics"
"Give me just the top 3 risk factors"
```

### 5. Combine Multiple Queries

```
"Show me the risk score for ABC-123 and compare it to XYZ-456"
"Generate a report covering both performance and risk for this deal"
```

## Troubleshooting

### "Connection Failed"

**Symptoms**: Red dot, "Connection Failed" status

**Solutions**:
1. Check API endpoint configuration
2. Verify API is deployed and running
3. Check internet connection
4. Try reconfiguring (click Session ID to reopen config)

### Messages Not Sending

**Symptoms**: Input doesn't clear, no response

**Solutions**:
1. Check connection status (should be green)
2. Wait for previous query to complete
3. Try refreshing the page
4. Check browser console for errors (F12)

### No Agent Response

**Symptoms**: Typing indicator doesn't appear or gets stuck

**Solutions**:
1. Check API logs in CloudWatch
2. Verify all Lambda functions are running
3. Check Bedrock service status
4. Try a simpler query first

### CORS Errors

**Symptoms**: Console shows "CORS policy" errors

**Solutions**:
1. Verify API Gateway has CORS enabled
2. Check allowed origins include your frontend URL
3. For local development, use the provided server script
4. Restart API Gateway if changes were made

### Session Expired

**Symptoms**: "No active session" message

**Solutions**:
1. Click "Clear Chat" to start fresh
2. Refresh the page
3. Sessions expire after 24 hours of inactivity
4. System will auto-create new session

## Configuration Options

### API Endpoint

The URL of your deployed API Gateway:

```
Format: https://[api-id].execute-api.[region].amazonaws.com/[stage]

Examples:
Production: https://abc123.execute-api.us-east-1.amazonaws.com/prod
Staging: https://abc123.execute-api.us-east-1.amazonaws.com/staging
Local: http://localhost:8000
```

### API Key (Optional)

If your API requires authentication:

1. Create API key in AWS Console
2. Associate with usage plan
3. Enter key in configuration modal
4. Key is stored in browser localStorage

**Security Note**: For production, use AWS Cognito for better security.

## Browser Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 90+ | ✅ Full |
| Edge | 90+ | ✅ Full |
| Firefox | 88+ | ✅ Full |
| Safari | 14+ | ✅ Full |
| Mobile | Latest | ✅ Responsive |

## Accessibility

- Keyboard navigation supported
- Semantic HTML structure
- ARIA labels for screen readers
- High contrast text
- Responsive font sizes

## Privacy & Security

- **Data Storage**: Session ID and config in localStorage only
- **Data Transmission**: All communication over HTTPS (in production)
- **Session Isolation**: Each session is independent
- **No Tracking**: No analytics or tracking scripts
- **Message History**: Stored server-side in DynamoDB

## Performance

- **Load Time**: < 2 seconds
- **Response Time**: Typically 2-10 seconds (depends on query complexity)
- **Agent Processing**: Parallel execution where possible
- **Message Limit**: 2000 characters per message
- **Session History**: Last 50 messages kept

## Next Steps

1. **Try the Quick Actions**: Test pre-built queries
2. **Explore Agent Cards**: Click to learn about each agent
3. **Use Suggestions**: Let AI guide your conversation
4. **Export & Review**: Save interesting conversations
5. **Integrate**: Use the API directly in your applications

## Additional Resources

- **API Documentation**: `/docs/multi_agent_system.md`
- **Agent Prompts**: `/src/prompt/`
- **Frontend Code**: `/src/frontend/`
- **Deployment Guide**: `/scripts/deploy_agents.sh`

## Support

For issues or questions:
1. Check browser console (F12)
2. Review API logs in CloudWatch
3. Verify configuration
4. Test with simple queries first
