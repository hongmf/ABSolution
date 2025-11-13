# ABSolution Dialogue Panel - Web UI

A modern, responsive web interface for interacting with the ABSolution Multi-Agent AI System.

## Features

### 🎨 Beautiful Interface
- Dark theme optimized for long sessions
- Smooth animations and transitions
- Responsive design for all screen sizes
- Real-time agent status indicators

### 💬 Chat Interface
- Natural conversation flow
- Message history
- Typing indicators
- Markdown formatting support
- Character counter

### 🤖 Agent Visualization
- See which agents are processing your query
- Visual feedback for active agents
- Agent descriptions and capabilities
- Real-time status updates

### ⚡ Quick Actions
- Pre-built query templates
- Export conversation history
- Clear chat
- Session management

### 🔧 Configuration
- Customizable API endpoint
- Optional API key authentication
- Local storage for settings
- Easy setup wizard

## Quick Start

### Option 1: Local Development Server

```bash
# Navigate to frontend directory
cd src/frontend

# Start Python HTTP server
python3 -m http.server 8080

# Open browser
open http://localhost:8080
```

### Option 2: Using Node.js

```bash
# Install http-server globally
npm install -g http-server

# Start server
cd src/frontend
http-server -p 8080

# Open browser
open http://localhost:8080
```

### Option 3: Direct File Access

Simply open `index.html` in your browser. However, you'll need CORS enabled on your API for this to work.

## Configuration

On first launch, you'll be prompted to configure:

1. **API Endpoint**: The URL of your deployed API Gateway
   - Format: `https://your-api-id.execute-api.region.amazonaws.com/prod`
   - For local testing: `http://localhost:8000`

2. **API Key** (optional): If your API requires authentication
   - Leave empty for public APIs

Settings are saved in browser localStorage.

### Example Configuration

```
API Endpoint: https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
API Key: (leave empty or enter your key)
```

## Usage

### Sending Messages

1. Type your question in the input field
2. Press **Ctrl+Enter** or click the send button
3. Watch as agents process your query
4. Review the response with agent attribution

### Example Queries

Try these example queries:

```
"What's the risk score for security ABC-123?"
"Show me all auto ABS deals from Q1 2024"
"Generate a deal analysis report"
"Compare performance vs. ABX.HE index"
"Alert me if default rates spike"
```

### Quick Actions

- **Recent Deals**: Query recent ABS issuances
- **Market Summary**: Get current market overview
- **High Risk Alerts**: View securities needing attention
- **Clear Chat**: Reset conversation
- **Export Chat**: Download conversation as Markdown

### Agent Cards

The left sidebar shows 5 specialized agents:

- **📊 Data Analyst** - Queries SEC filings
- **⚠️ Risk Assessor** - Evaluates credit risk
- **📝 Report Generator** - Creates reports
- **📈 Benchmark Analyst** - Compares performance
- **🔔 Alert Monitor** - Detects anomalies

Agent cards highlight when active, showing which agents are processing your query.

### Follow-up Suggestions

After receiving a response, the system may suggest relevant follow-up questions. Click any suggestion to automatically send it.

## File Structure

```
frontend/
├── index.html          # Main HTML structure
├── css/
│   └── styles.css      # All styling
├── js/
│   └── app.js          # Application logic & API calls
└── README.md           # This file
```

## Customization

### Changing Colors

Edit `css/styles.css` and modify the CSS variables:

```css
:root {
    --primary-color: #3B82F6;
    --secondary-color: #8B5CF6;
    --bg-primary: #0F172A;
    /* ... */
}
```

### Adding Features

The application is modular. Key functions in `js/app.js`:

- `sendMessage()` - Send user message
- `addMessage()` - Add message to chat
- `updateActiveAgents()` - Update agent status
- `showSuggestions()` - Display follow-ups

## API Integration

The UI communicates with the backend API using these endpoints:

### POST /session
Create a new conversation session

```javascript
{
  "user_id": "web_user_123"
}
```

### POST /message
Send a message

```javascript
{
  "session_id": "uuid",
  "message": "Your query here"
}
```

### POST /export
Export conversation

```javascript
{
  "session_id": "uuid",
  "format": "markdown"
}
```

## Deployment

### Deploy to S3 + CloudFront

```bash
# Build (if using build process)
# npm run build

# Upload to S3
aws s3 sync . s3://your-bucket-name/

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name your-bucket.s3.amazonaws.com
```

### Deploy to Amplify

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

### Deploy to Netlify/Vercel

Simply drag and drop the `frontend` folder to Netlify or Vercel.

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design

## Troubleshooting

### API Connection Failed

**Problem**: "Failed to connect to API"

**Solutions**:
1. Check API endpoint URL is correct
2. Verify API is deployed and running
3. Check CORS settings on API Gateway
4. Check browser console for detailed errors

### CORS Issues

If you see CORS errors:

1. Ensure API Gateway has CORS enabled
2. Check `Access-Control-Allow-Origin` headers
3. For local development, use a CORS proxy or run API locally

### Session Not Created

**Problem**: "No active session"

**Solutions**:
1. Check network connectivity
2. Verify API endpoint is reachable
3. Check browser console for errors
4. Try clearing localStorage and refreshing

### Messages Not Sending

**Problem**: Messages don't appear or get stuck

**Solutions**:
1. Check browser console for errors
2. Verify session is active
3. Refresh the page
4. Check API logs in CloudWatch

## Development

### Running Locally

```bash
# Start API locally (in another terminal)
cd src/agents
python -m flask run --port 8000

# Start frontend
cd src/frontend
python3 -m http.server 8080
```

### Testing

Open browser console and run:

```javascript
// Test session creation
createSession()

// Test message sending
sendQuickQuery("Test query")

// Check state
console.log(CONFIG)
console.log(state)
```

## Security Notes

- API keys are stored in browser localStorage (not recommended for production)
- Use proper authentication (Cognito, API keys) for production deployments
- Enable HTTPS for all production deployments
- Sanitize all user inputs (already implemented)

## Performance

- Lazy loading for chat history
- Optimized animations
- Minimal dependencies (vanilla JS, no frameworks)
- Efficient DOM updates

## Accessibility

- Semantic HTML
- Keyboard navigation support
- ARIA labels (can be improved)
- Screen reader compatible

## Future Enhancements

- [ ] Voice input support
- [ ] File attachments
- [ ] Multi-language support
- [ ] Dark/light theme toggle
- [ ] Advanced markdown rendering
- [ ] Chart/graph visualization
- [ ] WebSocket support for real-time updates
- [ ] Offline mode with service workers

## License

Part of ABSolution project.

## Support

For issues or questions:
1. Check API logs in CloudWatch
2. Review browser console errors
3. Verify API configuration
4. Check backend documentation: `/docs/multi_agent_system.md`
