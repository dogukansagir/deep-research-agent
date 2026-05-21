from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from graph import app as agent_app  
from pydantic import BaseModel

class ResearchRequest(BaseModel):
    query: str

app = FastAPI()

def stream_research(initial_state):
    final_state = {}
    for chunk in agent_app.stream(initial_state, stream_mode="updates"):
        node_name = list(chunk.keys())[0]
        final_state.update(chunk[node_name])
        yield f"data: {node_name}\n\n"
    
    import json
    yield f"data: {json.dumps({'answer': final_state['final_answer'], 'citations': [c.model_dump() for c in final_state['synthesized_answer'].citations]})}\n\n"

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