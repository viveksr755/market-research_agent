from typing import Any

from langchain.tools import tool
from openai import AsyncOpenAI

from settings import settings

def _get_value(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)

def _extract_sources(response) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []

    for output_item in response.output:
        # Citations are normally found on message content items.
        content_items = _get_value(output_item, "content", []) or []

        for content_item in content_items:
            annotations = _get_value(
                content_item,
                "annotations",
                [],
            ) or []

            for annotation in annotations:
                url = _get_value(annotation, "url")
                title = _get_value(annotation, "title", "")

                if url:
                    sources.append(
                        {
                            "title": title or "",
                            "url": url,
                        }
                    )

        # Some SDK/API versions may expose sources on the
        # web-search action itself.
        action = _get_value(output_item, "action")

        if action:
            action_sources = _get_value(action, "sources", []) or []

            for source in action_sources:
                url = _get_value(source, "url")
                title = _get_value(source, "title", "")

                if url:
                    sources.append(
                        {
                            "title": title or "",
                            "url": url,
                        }
                    )

    unique_sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for source in sources:
        url = source["url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)
        unique_sources.append(source)

    return unique_sources

def make_web_research(analysis_type: str):
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        max_retries=0,
    )

    @tool("web_research")
    async def web_research(query: str) -> dict:
        """
        Perform comprehensive web research for one analysis type.

        The delegated research request must be passed as one complete
        query. Do not split the request into multiple searches.
        """

        print(f"\n[WEB RESEARCH: {analysis_type}]")
        print(f"[QUERY] {query}")

        research_prompt = f"""
You are conducting {analysis_type} research.

Research request:

{query}

Perform comprehensive current web research for this request.

Return a detailed factual analysis appropriate for the
{analysis_type} analysis.

Important:
- Research the complete request.
- Do not ask follow-up questions.
- Do not leave important parts of the request unanswered.
- Prefer authoritative and recent sources.
- Distinguish factual information from estimates or claims.
- Include useful source URLs.
"""

        response = await client.responses.create(
            model=settings.OPENAI_MODEL,
            input=research_prompt,
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": "high",
                }
            ],
        )

        answer = response.output_text.strip()

        if not answer:
            raise RuntimeError(
                f"The {analysis_type} research call returned no text."
            )

        return {
            "analysis_type": analysis_type,
            "analysis": answer,
            "sources": _extract_sources(response),
        }

    return web_research
