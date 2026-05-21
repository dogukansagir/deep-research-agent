import httpx

url = "http://localhost:8000/research"
query = {"query": "how does flash attention work"}

with httpx.stream("POST", url, json=query, timeout=300) as response:
    for chunk in response.iter_text():
        if chunk.strip():
            print(chunk)