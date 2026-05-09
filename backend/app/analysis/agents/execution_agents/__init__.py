"""Execution agents package — real computational analysis implementations."""

from app.analysis.agents.execution_agents.statistical import StatisticalAgent
from app.analysis.agents.execution_agents.correlation import CorrelationAgent
from app.analysis.agents.execution_agents.pattern import PatternAgent
from app.analysis.agents.execution_agents.predictive import PredictiveAgent
from app.analysis.agents.execution_agents.nlp import NLPAgent
from app.analysis.agents.execution_agents.time_series import TimeSeriesAgent

__all__ = [
    "StatisticalAgent",
    "CorrelationAgent",
    "PatternAgent",
    "PredictiveAgent",
    "NLPAgent",
    "TimeSeriesAgent",
]
