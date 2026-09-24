from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend, StateBackend
from deepagents.middleware import SubAgent, SummarizationMiddleware
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from research.models import ResearchResult
from research.web_research import make_web_research
from settings import settings
from supervisor_prompt import SUPERVISOR_PROMPT

if not settings.OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. Add it to your .env file."
    )

def create_model(model_name: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        api_key=settings.OPENAI_API_KEY,
        streaming=False,
        max_retries=0,
    )

llm = create_model(settings.OPENAI_MODEL)

market_web_research = make_web_research("market")
competitor_web_research = make_web_research("competitor")
risk_web_research = make_web_research("risk")

market_agent = SubAgent(
    name="market_researcher",
    description=(
        "Performs Market / Product analysis using exactly "
        "one comprehensive web research call."
    ),
    model=llm,
    tools=[market_web_research],
    skills=["./skills/market_research/"],
    response_format=ResearchResult,
    system_prompt=(
        "Perform the delegated market analysis. "
        "Call web_research exactly once. "
        "Use its returned analysis and sources to construct "
        "ResearchResult, then return immediately."
    ),
    middleware=[
        ToolCallLimitMiddleware(
            tool_name="web_research",
            run_limit=1,
            exit_behavior="error",
        )
    ],
)

competitor_agent = SubAgent(
    name="competitor_researcher",
    description=(
        "Performs Competitor analysis using exactly "
        "one comprehensive web research call."
    ),
    model=llm,
    tools=[competitor_web_research],
    skills=["./skills/competitor_research/"],
    response_format=ResearchResult,
    system_prompt=(
        "Perform the delegated competitor analysis. "
        "Call web_research exactly once. "
        "Use its returned analysis and sources to construct "
        "ResearchResult, then return immediately."
    ),
    middleware=[
        ToolCallLimitMiddleware(
            tool_name="web_research",
            run_limit=1,
            exit_behavior="error",
        )
    ],
)

risk_agent = SubAgent(
    name="risk_researcher",
    description=(
        "Performs Risk / Market-Gap analysis using exactly "
        "one comprehensive web research call."
    ),
    model=llm,
    tools=[risk_web_research],
    skills=["./skills/risk_research/"],
    response_format=ResearchResult,
    system_prompt=(
        "Perform the delegated risk and market-gap analysis. "
        "Call web_research exactly once. "
        "Use its returned analysis and sources to construct "
        "ResearchResult, then return immediately."
    ),
    middleware=[
        ToolCallLimitMiddleware(
            tool_name="web_research",
            run_limit=1,
            exit_behavior="error",
        )
    ],
)

reports_directory = Path(settings.REPORTS_DIR).resolve()
reports_directory.mkdir(parents=True, exist_ok=True)

document_backend = LocalShellBackend(
    root_dir=str(reports_directory)
)

document_agent = SubAgent(
    name="document_generator",
    description=(
        "Generates the final DOCX report from completed research. "
        "It does not perform research."
    ),
    model=llm,
    skills=["./skills/document_generation/"],
)

checkpointer = MemorySaver()
supervisor_state_backend = StateBackend()

supervisor_agent = create_deep_agent(
    model=llm,
    system_prompt=SUPERVISOR_PROMPT,
    middleware=[
        SummarizationMiddleware(
            model=create_model(
                settings.OPENAI_SUMMARIZATION_MODEL
            ),
            trigger=("tokens", 4000),
            backend=supervisor_state_backend,
        ),
    ],
    subagents=[
        market_agent,
        competitor_agent,
        risk_agent,
        document_agent,
    ],
    backend=document_backend,
    checkpointer=checkpointer,
)
