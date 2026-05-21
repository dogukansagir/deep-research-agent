from schemas import AgentTask, AcademicSearchResult
import config
import httpx
from pydantic import BaseModel
from prompts import academic_search_prompt
from llm_client import llm_client
from langfuse import observe

class KeyFindings(BaseModel):
    key_findings: list[str]

def reconstruct_abstract(abstract_inverted_index: dict) -> str:
    if not abstract_inverted_index:
        return ""
    positions = {}
    for word, indices in abstract_inverted_index.items():
        for idx in indices:
            positions[idx] = word
    return " ".join(positions[i] for i in sorted(positions.keys()))

@observe()
def findings_extraction(paper: dict) -> AcademicSearchResult:
    result = None
    abstract = reconstruct_abstract(paper.get("abstract_inverted_index", {}))
    if not abstract:
        return result
    url = paper.get("primary_location", {}) or {}
    url = url.get("landing_page_url", "")
    authors = [a["author"]["display_name"] for a in paper.get("authorships", [])]
    findings = llm_client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        response_model=KeyFindings,
        messages=[{"role": "user", "content": academic_search_prompt(abstract)}]
    )
    result = AcademicSearchResult(
        url=url,
        title=paper.get("display_name", ""),
        authors=authors,
        publication_year=paper.get("publication_year", 0),
        abstract=abstract,
        key_findings=findings.key_findings
    )
    return result

@observe()
def academic_search_agent(task: AgentTask) -> dict:
    response = httpx.get(
        config.OPENALEX_URL,
        params={
            "search": task.query,
            "per_page": 5,
        }
    )
    results = []
    papers = response.json().get("results", [])
    for paper in papers:
        result = findings_extraction(paper)
        if result is not None:
            results.append(result)
    
    return {"academic_results": results}