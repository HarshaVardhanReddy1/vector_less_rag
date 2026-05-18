from openai import OpenAI
import json
from dotenv import load_dotenv
import os
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


def generate_response(prompt):

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages = [{"role": "user", "content": prompt}]
        )

        output = response.choices[0].message.content.strip()

        return output

    except Exception as e:
        return json.dumps({
            "error": str(e)
        })

 