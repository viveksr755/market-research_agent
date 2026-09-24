from typing import Literal

from pydantic import BaseModel, Field


class ResearchResult(BaseModel):

    analysis_type: Literal[
        "market",
        "competitor",
        "risk",
    ]

    analysis: str

    sources: list[dict[str, str]] = Field(
        default_factory=list
    )