import anthropic
import os

def call_claude(prompt, data_summary, api_key):
    """Call Claude with visualization prompt and data"""
    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[{
            "role": "user", 
            "content": f"{prompt}\n\nAnalyze this data and recommend visualizations:\n{data_summary}"
        }]
    )
    
    return message.content[0].text

# Usage in notebook:
# from claude_viz import call_claude
# api_key = "your-anthropic-api-key"
# recommendations = call_claude(viz_prompt, data_summary, api_key)