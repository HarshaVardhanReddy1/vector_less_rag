from page_index_rebuilt.config import DEFAULT_TREE_PATH
from page_index_rebuilt.pipeline import answer_from_pages_json, build_index

def main():
    if DEFAULT_TREE_PATH.exists():
        print(f"Using existing tree index: {DEFAULT_TREE_PATH}")
    else:
        print("Tree index not found. Building index from pages...")
        index_info = build_index()
        print("Index built successfully:")
        print(index_info)

    query = "What is progressive bounding?"
    print(f"\nAnswering query: {query!r}")
    answer_info = answer_from_pages_json(query=query)
    print("Query answered successfully:")
    print(answer_info)

if __name__ == "__main__":
    main()
