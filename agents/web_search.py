from tavily import TavilyClient
import config
from schemas import AgentTask, WebSearchResult
from typing import Literal
from urllib.parse import urlparse

client = TavilyClient(api_key=config.TAVILY_API_KEY)
FORUM_DOMAINS = {"reddit.com", "stackoverflow.com", "news.ycombinator.com", "quora.com", "discourse.org"}
DOCS_DOMAINS = {"docs.", "documentation.", "readthedocs.io", "devdocs.io"}
NEWS_DOMAINS = {"bbc.com", "cnn.com", "reuters.com", "theguardian.com", "nytimes.com", "techcrunch.com", "wired.com"}
BLOG_KEYWORDS = {"blog", "medium.com", "substack.com", "hashnode.dev", "dev.to", "towards"}

def guess_source_type(url: str) -> Literal["blog", "docs", "forum", "news", "other"]:
    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")

    if any(f in domain for f in FORUM_DOMAINS):
        return "forum"
    if any(d in domain for d in DOCS_DOMAINS):
        return "docs"
    if any(n in domain for n in NEWS_DOMAINS):
        return "news"
    if any(b in domain or b in parsed.path.lower() for b in BLOG_KEYWORDS):
        return "blog"
    return "other"

def web_search_agent(task: AgentTask) -> list[WebSearchResult]:
    search_results = client.search(task.query, num_results=10)
    web_results = []
    for result in search_results:
        web_results.append(WebSearchResult(
            url=result["url"],
            title=result["title"],
            content=result["content"],
            source_type=guess_source_type(result["url"]),
            relevancy_score=result["score"]
        ))
    return web_results