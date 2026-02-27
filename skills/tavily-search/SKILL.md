---
name: tavily-search
description: "AI-optimized web search with structured results for LLM context. Tavily aggregates multiple sources, extracts key content, and returns clean markdown-formatted results perfect for research and knowledge synthesis."
homepage: https://tavily.com
metadata:
  openclaw:
    emoji: 🔍
    requires:
      env:
        - TAVILY_API_KEY
      bins:
        - python3
      anyBins:
        - pip
        - pip3
    primaryEnv: TAVILY_API_KEY
    install:
      - type: brew
        pkg: python@3.11
      - type: pip
        pkg: tavily-python
      - type: pip
        pkg: requests
---

# Tavily Search

AI-optimized web search that returns structured, LLM-ready results. Tavily aggregates sources, extracts content, and formats everything in clean markdown — perfect for research workflows.

## When to Use

✅ **USE this skill when:**
- Deep research on any topic
- Need aggregated search results with sources
- Want clean markdown content (no HTML parsing)
- Building knowledge bases or reports
- Fact-checking with citations

❌ **DON'T use when:**
- Real-time news (use direct news APIs)
- Very specific local business info (use Google Maps)
- Image/video search (Tavily is text-focused)

## Quick Start

### 1. Get API Key

```bash
# Sign up at https://tavily.com (free tier: 1,000 calls/month)
# Store in OpenClaw:
openclaw configure --section skills --set tavily.apiKey=tvly-xxxxxxxx
```

### 2. Basic Search

```python
from tavily_client import TavilyClient

client = TavilyClient()
results = client.search("quantum computing breakthroughs 2024")

for r in results["results"]:
    print(f"- {r['title']}: {r['url']}")
    print(f"  {r['content'][:200]}...")
```

### 3. Deep Research Mode

```python
# Tavily's advanced search with more context
results = client.search(
    query="climate change economic impact",
    search_depth="deep",  # deep | basic
    include_answer=True,   # AI-generated summary
    include_raw_content=True,  # Full page content
    max_results=10
)

print(results["answer"])  # Synthesized answer
```

## API Reference

### `TavilyClient.search(query, **options)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | Search query |
| `search_depth` | str | "basic" | "ultra-fast", "fast", "basic" or "advanced" |
| `include_answer` | bool | False | Include AI-generated answer |
| `include_raw_content` | bool | False | Include full page content |
| `max_results` | int | 5 | Number of results (1-20) |
| `include_domains` | list | None | Restrict to specific domains |
| `exclude_domains` | list | None | Exclude specific domains |

### Response Format

```json
{
  "query": "your search query",
  "answer": "AI-generated summary (if requested)",
  "results": [
    {
      "title": "Page Title",
      "url": "https://example.com/article",
      "content": "Clean extracted content...",
      "raw_content": "Full page HTML converted to markdown...",
      "score": 0.95,
      "published_date": "2024-01-15"
    }
  ]
}
```

## Use Cases

### Research Report Generation

```python
# Gather sources for a comprehensive report
topics = [
    "AI agent frameworks 2024",
    "LLM orchestration patterns",
    "Multi-agent system architectures"
]

all_results = []
for topic in topics:
    results = client.search(
        topic,
        search_depth="deep",
        include_answer=True,
        max_results=5
    )
    all_results.append({
        "topic": topic,
        "summary": results.get("answer", ""),
        "sources": results["results"]
    })

# Generate markdown report
report = generate_markdown_report(all_results)
```

### Competitive Intelligence

```python
# Monitor competitor mentions
competitors = ["competitor1.com", "competitor2.com"]

for competitor in competitors:
    results = client.search(
        f"site:{competitor} product launch",
        max_results=10,
        include_raw_content=True
    )
    analyze_mentions(results)
```

### Knowledge Base Building

```python
# Populate internal knowledge base
questions = load_faq_questions()

for q in questions:
    results = client.search(q, include_answer=True)
    kb_entry = {
        "question": q,
        "answer": results.get("answer"),
        "sources": [r["url"] for r in results["results"]]
    }
    save_to_kb(kb_entry)
```

### Fact Verification

```python
# Verify claims with multiple sources
claim = "Company X acquired Company Y for $1B"
results = client.search(claim, max_results=10)

# Cross-reference sources
verification = cross_reference_claim(claim, results["results"])
confidence_score = verification["confidence"]
sources = verification["supporting_sources"]
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `TavilyAuthError` | Invalid API key | Check TAVILY_API_KEY |
| `TavilyRateLimitError` | Quota exceeded | Wait or upgrade plan |
| `TavilyTimeoutError` | Request timeout | Retry with smaller max_results |
| `TavilySearchError` | Invalid query | Check query format |

## Pricing

- **Free**: 1,000 API calls/month
- **Pro**: $0.025/call (pay-as-you-go)
- **Enterprise**: Custom pricing

## Integration Examples

### With OpenClaw Sessions

```python
# Use in a sub-agent for parallel research
sessions_spawn(
    agentId="research-agent",
    task="Research: 'latest Python async patterns'. Use Tavily search.",
    label="async-research"
)
```

### With Document Processing

```python
# Enrich documents with web sources
doc = load_document("report.pdf")
key_claims = extract_claims(doc)

for claim in key_claims:
    sources = client.search(claim["text"], max_results=3)
    claim["sources"] = sources["results"]

save_enriched_document(doc)
```

## CLI Usage

```bash
# Quick search
python tavily_client.py "quantum computing"

# Deep search with answer
python tavily_client.py "climate change solutions" --deep --answer

# Save to file
python tavily_client.py "AI safety" --output research.md
```

---

**Last Updated:** 2026-02-26 | **Status:** Production Ready
