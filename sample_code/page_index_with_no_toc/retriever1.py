import json

from sample_code.page_index_with_no_toc.utils import load_json_data
from sample_code.page_index_with_no_toc.open_ai_llm import generate_response
from sample_code.page_index_with_no_toc.prompts import generate_relevant_node, generate_answer_prompt


def get_answer(tree_path, pages_path, query="what is Rules of Practice and Procedure"):

    # Load JSON files
    tree_data = load_json_data(tree_path)
    pages_data = load_json_data(pages_path)

    # Generate prompt for relevant node
    relevant_node_prompt = generate_relevant_node(tree_data, query)

    # Get relevant node response from LLM
    relevant_node_response = generate_response(relevant_node_prompt)

    print("Relevant Node Response:")
    print(relevant_node_response)

    # Convert JSON string -> Python dictionary
    node_data = json.loads(relevant_node_response)

    # Handle empty response
    if node_data == []:
        return "No relevant node found."

    # Extract context
    context = get_context_from_node(node_data, pages_data)
    print(context)

    # Generate answer prompt
    answer_prompt = generate_answer_prompt(context, query)

    # Generate final answer
    response = generate_response(answer_prompt)

    print("\nFinal Answer:")
    print(response)

    return response


def get_context_from_node(node, pages_data):

    start_page = int(node["start_index"])
    end_page = int(node["end_index"])

    context = []

    for i in range(start_page-1, end_page ):

        # Assuming pages_data is a list
        context.append(pages_data[i]["page_text"])

    return "\n".join(context)


get_answer(
    "json_files/tree_from_toc1.json",
    "json_files/pdf_pages1.json"
)