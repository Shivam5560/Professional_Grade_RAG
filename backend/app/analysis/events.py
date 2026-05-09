"""
Workflow event / result types for the analysis pipeline.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class AnalysisTask:
    task_id: str
    description: str
    required_agents: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDecomposedResult:
    tasks: List[AnalysisTask]


@dataclass
class ContextBuiltResult:
    dataset_ref: str
    profile_json: Dict[str, Any]
    columns: List[str]
    row_count: int
    data_quality: Optional[Any] = None  # DataQualityReport — set after pipeline runs


@dataclass
class AgentInvocation:
    agent_name: str
    task_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyPlannedResult:
    invocations: List[AgentInvocation]


@dataclass
class AgentFinding:
    metric: str
    value: Any
    description: str
    significance: float


@dataclass
class AgentResult:
    agent_name: str
    task_id: str
    findings: List[AgentFinding]
    confidence: float


@dataclass
class ExecutionCompleteResult:
    results: List[AgentResult]


@dataclass
class Insight:
    insight_id: str
    content: str
    significance_score: float
    source_agents: List[str]
    data_evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InsightsPrioritizedResult:
    insights: List[Insight]


@dataclass
class ReportSection:
    title: str
    content: str
    chart_id: str = ""


@dataclass
class NarrativeGeneratedResult:
    executive_summary: str
    sections: List[ReportSection]


@dataclass
class DesignSpec:
    theme: str
    color_palette: List[str]
    layout: str
    chart_specs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AnalysisCompleteResult:
    report_id: str
    narrative: str
    sections: List[Dict[str, Any]]
    insights: List[Dict[str, Any]]
    chart_specs: List[Dict[str, Any]]
    design_spec: Dict[str, Any]
