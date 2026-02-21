from .intake import IntakeAgent
from .data_processor import DataProcessorAgent
from .research import ResearchAgent
from .frameworks import FrameworksAgent
from .financial import FinancialAgent
from .benchmarking import BenchmarkingAgent
from .red_team import RedTeamAgent
from .synthesis import SynthesisAgent
from .writer import WriterAgent
from .communications import CommunicationsAgent

ALL_AGENTS = {
    "intake":          IntakeAgent,
    "data_processor":  DataProcessorAgent,
    "research":        ResearchAgent,
    "frameworks":      FrameworksAgent,
    "financial":       FinancialAgent,
    "benchmarking":    BenchmarkingAgent,
    "red_team":        RedTeamAgent,
    "synthesis":       SynthesisAgent,
    "writer":          WriterAgent,
    "communications":  CommunicationsAgent,
}
