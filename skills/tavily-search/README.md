# Tavily Search Skill

AI-optimized web search with structured results for LLM context.

## Quick Start

```bash
# Set API key
export TAVILY_API_KEY="tvly-your-key-here"

# Basic search
python tavily_client.py "quantum computing breakthroughs"

# Deep search with AI answer
python tavily_client.py "climate change economic impact" --deep --answer

# Save to file
python tavily_client.py "AI safety research" --deep --output report.md
```

## Python API

```python
from tavily_client import TavilyClient

client = TavilyClient()

# Basic search
results = client.search("Python async patterns")

# Deep research mode
research = client.search(
    "blockchain interoperability 2024",
    search_depth="deep",
    include_answer=True,
    max_results=10
)

print(research.answer)  # AI-generated summary
for r in research.results:
    print(f"- {r.title}: {r.url}")
```

## Installation

```bash
pip install tavily-python requests
```

Or use the skill's install directive (OpenClaw handles this automatically).

## API Key

Get your free API key at [tavily.com](https://tavily.com) — 1,000 calls/month on free tier.
