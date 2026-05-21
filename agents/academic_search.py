from schemas import AgentTask, AcademicSearchResult
import config
import httpx
from pydantic import BaseModel
from prompts import academic_search_prompt
from llm_client import llm_client

class KeyFindings(BaseModel):
    key_findings: list[str]

def academic_search_agent(task: AgentTask) -> dict[str, list[AcademicSearchResult]]:
    response = httpx.get(
    config.SEMANTIC_SCHOLAR_URL,
    params={
        "query": task.query,
        "limit": 5,
        "fields": "title,authors,year,abstract,url"
    }
    )
    results = []
    for paper in response.json().get("data", []):
        if not paper.get("abstract"):
            continue
        findings = llm_client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            response_model=KeyFindings,
            messages=[{"role": "user", "content": academic_search_prompt(paper['abstract'])}]
        )
        results.append(AcademicSearchResult(
            url=paper["url"],
            title=paper["title"],
            authors=[author["name"] for author in paper["authors"]],
            year=paper["year"],
            abstract=paper["abstract"],
            key_findings=findings.key_findings
        ))
    return {"academic_results": results}