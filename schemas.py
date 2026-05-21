from pydantic import BaseModel, Field
from typing import Literal, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator

class AgentTask(BaseModel):
    task_agent: Literal["web_search_agent", "academic_search_agent", "code_agent"]
    query: str
    reasoning: str = Field(..., description="The reasoning behind the choice of the agent for the given query.")

class ExecutionPlan(BaseModel):
    tasks: list[AgentTask]
    query_complexity: Literal["simple", "moderate", "complex"] = Field(..., description="The complexity level of the query.")

class WebSearchResult(BaseModel):
    url: str
    title: str
    content: str
    source_type: Literal["blog", "docs", "forum", "news", "other"]
    relevancy_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the relevancy of the search result to the original query.")

class AcademicSearchResult(BaseModel):
    title: str
    authors: list[str]
    publication_year: int
    abstract: str
    url: str
    key_findings: list[str]

class CodeResult(BaseModel):
    code: str
    language: str
    explanation: str

class Citation(BaseModel):
    position: int
    title: str
    url: str
    source_type: Literal["web", "academic", "code"]

class SynthesizedAnswer(BaseModel):
    answer: str
    citations: list[Citation] = Field(..., description="A list of URLs or references that were used to synthesize the final answer.")
    confidence_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the confidence level of the synthesizer agent.")

class EvalResult(BaseModel):
    faithfulness_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the faithfulness of the synthesized answer to the original query and the provided evidence.")
    answer_relevance_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the relevance of the synthesized answer to the original query.")
    answer_completeness_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the completeness of the synthesized answer in addressing all aspects of the original query.")
    overall_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the overall quality of the synthesized answer based on the evaluation criteria.")
    should_retry: bool = Field(..., description="A boolean indicating whether the evaluation suggests that the synthesizer agent should attempt to generate a new answer based on the feedback.")
    reasoning: str = Field(..., description="Detailed feedback on the agent's performance based on the evaluation criteria.")

class AgentState(TypedDict):
    query: str
    execution_plan: ExecutionPlan
    web_results: Annotated[list[WebSearchResult], operator.add]
    academic_results: Annotated[list[AcademicSearchResult], operator.add]
    code_results: CodeResult | None
    synthesized_answer: SynthesizedAnswer
    eval_result: EvalResult
    retry_count: int
    final_answer: str | None
    conversation_history: Annotated[Sequence[BaseMessage], add_messages]