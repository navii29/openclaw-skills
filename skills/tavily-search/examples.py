"""
Examples for Tavily Search Skill
"""

from tavily_client import TavilyClient


def example_basic_search():
    """Basic search usage"""
    client = TavilyClient()
    
    results = client.search("OpenAI GPT-5 rumors")
    
    print(f"Query: {results.query}")
    print(f"Found {len(results.results)} results\n")
    
    for r in results.results:
        print(f"- {r.title}")
        print(f"  {r.url}")
        print(f"  Score: {r.score:.2f}")
        print(f"  {r.content[:150]}...\n")


def example_deep_research():
    """Deep research with AI answer"""
    client = TavilyClient()
    
    results = client.search(
        "quantum computing breakthroughs 2024",
        search_depth="deep",
        include_answer=True,
        include_raw_content=True,
        max_results=10
    )
    
    print("=== AI Summary ===")
    print(results.answer)
    print("\n=== Sources ===")
    
    for r in results.results:
        print(f"\n{r.title}")
        print(f"Relevance: {r.score:.2f}")
        print(f"URL: {r.url}")


def example_competitive_intelligence():
    """Monitor competitor mentions"""
    client = TavilyClient()
    
    competitors = ["openai.com", "anthropic.com"]
    
    for competitor in competitors:
        print(f"\n=== {competitor} ===")
        results = client.search(
            f"site:{competitor} product announcement",
            max_results=5
        )
        for r in results.results:
            print(f"- {r.title}")


def example_domain_restricted():
    """Search within specific domains"""
    client = TavilyClient()
    
    results = client.search(
        "machine learning tutorials",
        include_domains=["arxiv.org", "paperswithcode.com"],
        max_results=10
    )
    
    for r in results.results:
        print(f"- {r.title}")
        print(f"  {r.url}\n")


def example_markdown_export():
    """Export results as markdown"""
    client = TavilyClient()
    
    results = client.search(
        "renewable energy trends 2024",
        search_depth="deep",
        include_answer=True,
        max_results=8
    )
    
    markdown = results.to_markdown()
    
    with open("research_report.md", "w", encoding="utf-8") as f:
        f.write(markdown)
    
    print("Saved to research_report.md")


def example_fact_checking():
    """Verify claims with sources"""
    client = TavilyClient()
    
    claims = [
        "Tesla FSD accidents 2024",
        "SpaceX Starship launch success rate"
    ]
    
    for claim in claims:
        print(f"\n=== Fact Check: {claim} ===")
        results = client.search(claim, max_results=5)
        
        for r in results.results:
            print(f"- {r.title} ({r.score:.2f})")
            print(f"  {r.url}")


if __name__ == "__main__":
    print("Tavily Search Examples")
    print("=" * 50)
    
    # Run examples
    # example_basic_search()
    # example_deep_research()
    # example_competitive_intelligence()
    # example_domain_restricted()
    # example_markdown_export()
    # example_fact_checking()
    
    print("\nUncomment the example you want to run in __main__")
