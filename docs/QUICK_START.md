# ABSolution Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Deploy the Multi-Agent System

```bash
# Navigate to project root
cd ABSolution

# Run deployment script
./scripts/deploy_agents.sh

# Note the API endpoint from output
# Example: https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

**What this does:**
- ✅ Deploys Lambda functions for all 5 agents
- ✅ Creates DynamoDB tables for conversation state
- ✅ Sets up API Gateway with REST endpoints
- ✅ Configures Step Functions for orchestration
- ✅ Sets up EventBridge rules for automation

---

### Step 2: Launch the Dialogue Panel

```bash
# Start the web UI server
python3 scripts/serve_ui.py

# You'll see:
# 🌐 Open in browser: http://localhost:8080
```

Open your browser and navigate to **http://localhost:8080**

---

### Step 3: Configure and Start Chatting

**On first launch:**

1. **Configure API Endpoint**
   - A modal will appear
   - Enter your API Gateway endpoint (from Step 1)
   - Example: `https://abc123.execute-api.us-east-1.amazonaws.com/prod`
   - Click "Save"

2. **Start Chatting!**
   - Type your question in the input box
   - Press **Ctrl+Enter** or click Send
   - Watch the agents work their magic

---

## 📋 Example Queries to Try

### 1. Data Query
```
"Show me all auto ABS deals from Q1 2024"
```
**Agent Used:** 📊 Data Analyst
**Response:** List of securities with key metrics

---

### 2. Risk Assessment
```
"What's the risk score for security ABC-123?"
```
**Agents Used:** ⚠️ Risk Assessor + 📊 Data Analyst
**Response:** Risk score (0-100) with detailed analysis

---

### 3. Generate Report
```
"Generate a deal analysis report for security ABC-123"
```
**Agents Used:** 📝 Report Generator + ⚠️ Risk Assessor + 📊 Data Analyst
**Response:** Comprehensive formatted report

---

### 4. Benchmark Analysis
```
"Compare security ABC-123 to similar vintage deals"
```
**Agents Used:** 📈 Benchmark Analyst + 📊 Data Analyst
**Response:** Comparative analysis with peer group

---

### 5. Set Alert
```
"Alert me if default rates spike above 5%"
```
**Agent Used:** 🔔 Alert Monitor
**Response:** Alert confirmation and monitoring details

---

## 🎯 Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  ABSolution                    🟢 Connected   Session: abc123... │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                   │
│  AGENTS      │                CHAT AREA                         │
│              │                                                   │
│ 📊 Data      │  ┌──────────────────────────────────────────┐   │
│   Analyst    │  │ Welcome to ABSolution!                   │   │
│              │  │ I coordinate 5 AI agents to help you... │   │
│ ⚠️  Risk     │  └──────────────────────────────────────────┘   │
│   Assessor   │                                                   │
│              │  You: What's the risk score for ABC-123?         │
│ 📝 Report    │                                                   │
│   Generator  │  ┌──────────────────────────────────────────┐   │
│              │  │ AI: The risk score is 45 (Medium)...    │   │
│ 📈 Benchmark │  │ [⚠️ Risk Assessor] [📊 Data Analyst]     │   │
│   Analyst    │  └──────────────────────────────────────────┘   │
│              │                                                   │
│ 🔔 Alert     │  Suggested: "What are the main risk factors?"    │
│   Monitor    │                                                   │
│              │  ┌──────────────────────────────────────────┐   │
│              │  │ Type your message...             [Send ➤]│   │
│              │  └──────────────────────────────────────────┘   │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 💡 Tips for Best Results

### 1. Be Specific
```
❌ "Tell me about ABS"
✅ "Show me auto ABS deals issued in Q1 2024 with AAA rating"
```

### 2. Use Context
The system remembers your conversation:
```
You: "Show me security ABC-123"
You: "What's its risk score?"  ← No need to repeat "ABC-123"
You: "Compare to market average" ← Still knows the context
```

### 3. Use Quick Actions
Click sidebar buttons for common queries:
- **Recent Deals**
- **Market Summary**
- **High Risk Alerts**

### 4. Export Important Conversations
Click "Export Chat" to download as Markdown

---

## 🔧 Troubleshooting

### "Connection Failed"
**Problem:** Red dot, can't connect to API

**Solution:**
1. Check API endpoint is correct
2. Verify API Gateway is deployed
3. Check AWS credentials
4. Review CloudWatch logs

### "No Response"
**Problem:** Message sent but no response

**Solution:**
1. Check Bedrock is enabled in your region
2. Verify Lambda functions are running
3. Check CloudWatch logs for errors
4. Try a simpler query first

### CORS Errors
**Problem:** Browser shows CORS policy errors

**Solution:**
1. Ensure API Gateway has CORS enabled
2. Use the provided server script (`serve_ui.py`)
3. Don't open HTML directly in browser

---

## 📊 What Each Agent Does

| Agent | Purpose | Example Use Case |
|-------|---------|------------------|
| 📊 **Data Analyst** | Query SEC filings, extract metrics | "Show me deals from Q1" |
| ⚠️ **Risk Assessor** | Calculate risk scores, assess quality | "What's the risk score?" |
| 📝 **Report Generator** | Create narrative reports | "Generate a report" |
| 📈 **Benchmark Analyst** | Compare performance | "Compare to peers" |
| 🔔 **Alert Monitor** | Detect anomalies, set alerts | "Alert me if..." |

---

## 🎨 Dialogue Panel Features

✅ **Dark Theme** - Easy on the eyes for long sessions
✅ **Real-time Status** - See which agents are working
✅ **Smart Suggestions** - AI suggests follow-up questions
✅ **Export Conversations** - Save as Markdown
✅ **Message History** - Full conversation context
✅ **Typing Indicators** - Know when agents are processing
✅ **Agent Attribution** - See which agents contributed
✅ **Responsive Design** - Works on mobile, tablet, desktop

---

## 📚 Next Steps

1. **Explore the Agents**
   - Try different query types
   - See how agents coordinate
   - Use follow-up suggestions

2. **Read Documentation**
   - [Multi-Agent System](multi_agent_system.md) - Technical details
   - [Dialogue Panel Guide](dialogue_panel_guide.md) - Complete UI guide

3. **Deploy to Production**
   - Configure Bedrock access
   - Set up SageMaker models
   - Deploy to S3 + CloudFront

4. **Customize**
   - Modify agent prompts in `src/prompt/`
   - Adjust UI theme in `src/frontend/css/styles.css`
   - Add new agents or capabilities

---

## 🆘 Need Help?

**Check these resources:**
- API logs: AWS CloudWatch → Lambda logs
- Frontend: Browser console (F12)
- Configuration: Click Session ID to reconfigure
- Documentation: `/docs/` folder

**Common Issues:**
1. **Can't connect:** Check API endpoint configuration
2. **Slow responses:** Check Lambda memory/timeout settings
3. **No agents active:** Verify Bedrock service is enabled
4. **Session expired:** Refresh page (sessions last 24 hours)

---

## ⚡ Pro Tips

**Keyboard Shortcuts:**
- `Ctrl+Enter` - Send message
- `Esc` - Clear input

**Quick Actions:**
- Click example queries in welcome message
- Use sidebar quick action buttons
- Click suggested follow-ups

**Agent Coordination:**
- Complex queries use multiple agents
- Agents run in parallel when possible
- Each response shows which agents contributed

---

## 🎉 You're Ready!

Start by trying one of these:

```
"Show me all auto ABS deals from Q1 2024"
"What's the risk score for security ABC-123?"
"Generate a market summary report"
```

Have fun exploring the multi-agent system! 🚀
