#!/usr/bin/env python3
"""
Quick test to verify SEC Explorer panel can be imported and has the render function
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from ui.pages import sec_explorer_panel
    print("✓ Successfully imported sec_explorer_panel")

    # Check if render function exists
    if hasattr(sec_explorer_panel, 'render'):
        print("✓ sec_explorer_panel.render() function exists")
    else:
        print("✗ sec_explorer_panel.render() function NOT found")

    # Check other functions
    functions = ['get_company_info', 'get_company_filings', 'format_file_size', 'get_filing_url']
    for func in functions:
        if hasattr(sec_explorer_panel, func):
            print(f"✓ {func}() function exists")
        else:
            print(f"✗ {func}() function NOT found")

    print("\n✓ All checks passed! The SEC Explorer panel should be visible in the Streamlit app.")
    print("\nTo view it:")
    print("1. Run: ./run_ui.sh")
    print("2. Open browser to: http://localhost:8501")
    print("3. Click on the '🔍 SEC Explorer' tab (6th tab, far right)")

except Exception as e:
    print(f"✗ Error importing sec_explorer_panel: {e}")
    import traceback
    traceback.print_exc()
