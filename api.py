from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from graph import app as agent_app  
from pydantic import BaseModel
from langfuse import observe, get_client
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

class ResearchRequest(BaseModel):
    query: str

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

def format_response(answer, citations):
    formatted_citations = " | ".join([f"{citation.position}. {citation.title} ({citation.url})" for citation in citations])
    return f"Answer: {answer} Citations: {formatted_citations}"

@observe(name="research_pipeline")
def stream_research(initial_state):
    langfuse = get_client()
    langfuse.update_current_span(name=f"research: {initial_state['query']}")
    final_state = {}
    for chunk in agent_app.stream(initial_state, stream_mode="updates"):
        node_name = list(chunk.keys())[0]
        final_state.update(chunk[node_name])
        yield f"data: {node_name}\n\n"
    
    yield f"data: {format_response(final_state['final_answer'], final_state['synthesized_answer'].citations)}\n\n"

@app.post("/research")
def research(request: ResearchRequest):
    initial_state = {
        "query": request.query,
        "execution_plan": None,
        "web_results": [],
        "academic_results": [],
        "code_result": None,
        "synthesized_answer": None,
        "eval_result": None,
        "retry_count": 0,
        "final_answer": None,
        "conversation_history": []
    }
    return StreamingResponse(
        stream_research(initial_state),
        media_type="text/event-stream"
        )