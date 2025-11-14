"""
AI Agent Prompts for ABSolution
Specialized prompts for different agent roles
"""

from . import data_analyst_prompt
from . import risk_assessor_prompt
from . import report_generator_prompt
from . import benchmark_analyst_prompt
from . import alert_monitor_prompt

__all__ = [
    'data_analyst_prompt',
    'risk_assessor_prompt',
    'report_generator_prompt',
    'benchmark_analyst_prompt',
    'alert_monitor_prompt'
]
