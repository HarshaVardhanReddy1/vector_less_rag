import ollama
import json


client = ollama.Client()


def generate_response(prompt, model="qcwind/qwen2.5-7B-instruct-Q4_K_M"):

    try:
        response = client.generate(
            model=model,
            prompt=prompt,

            options={
                "temperature": 0,
                "top_p": 0.1,
                "num_predict": 2000,
            }
        )

        output = response["response"].strip()

        return output

    except Exception as e:
        return json.dumps({
            "error": str(e)
        })