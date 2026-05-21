import instructor
import config
from openai import OpenAI

llm_client = instructor.from_openai(
    OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_API_URL),
    mode=instructor.Mode.JSON
)