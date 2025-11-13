def get_code_generation_prompt(data_context: str = "") -> str:
    """Generate prompt that asks Claude to create plotting code"""
    
    prompt = f"""
You are a data visualization expert. Given the following data context, generate complete Python plotting code.

{data_context}

REQUIREMENTS:
1. Generate executable matplotlib/seaborn code
2. Use 'df' as the dataframe variable
3. Create 2-3 appropriate visualizations
4. Include proper titles, labels, and formatting
5. Use plt.show() to display plots

FORMAT YOUR RESPONSE AS:
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Your plotting code here
plt.figure(figsize=(12, 8))
# ... visualization code ...
plt.show()
```

Generate the code now:
"""
    return prompt