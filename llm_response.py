from typing import List, Dict, Any
from openai import OpenAI
import config
from retriever import text_query_to_results

client = OpenAI(api_key=config.OPENAI_API_KEY)

def generate_response(user_query: str) -> Dict[str, Any]:
    """
    Generates a response to the user query using RAG.
    
    Args:
        user_query: The user's natural language query.
        
    Returns:
        A dictionary containing:
        - 'answer': The LLM's generated answer.
        - 'sources': A list of retrieved documents/tickets.
    """
    
    # 1. Retrieve relevant documents
    print(f"Retrieving documents for: {user_query}")
    retrieved_results = text_query_to_results(user_query, top_n=5)
    
    # 2. Construct the prompt
    context_str = ""
    if isinstance(retrieved_results, list) and retrieved_results:
        for i, res in enumerate(retrieved_results):
            context_str += f"Source {i+1}:\n"
            context_str += f"Title: {res.get('title', 'N/A')}\n"
            context_str += f"Type: {res.get('type', 'N/A')}\n"
            context_str += f"Tags: {', '.join(res.get('tags', []))}\n"
            # Add relationships if available to give more context
            rels = res.get('relationships', [])
            if rels:
                rel_desc = [f"{r['relationship']} -> {r['node_props'].get('name', 'Unknown')}" for r in rels]
                context_str += f"Relationships: {'; '.join(rel_desc)}\n"
            context_str += "\n"
    else:
        context_str = "No specific documents found."

    system_prompt = """You are a helpful AI assistant for a project management system. 
    You answer questions based on the provided retrieved tickets/documents.
    If the answer is not in the documents, say so, but try to be helpful.
    Cite your sources by referring to "Source X" when appropriate.
    """

    user_prompt = f"""
    User Query: {user_query}

    Retrieved Context:
    {context_str}

    Please answer the user's query based on the context above.
    """

    # 3. Call LLM
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"Error generating response: {str(e)}"

    return {
        "answer": answer,
        "sources": retrieved_results
    }

if __name__ == "__main__":
    # Test locally
    test_query = "Show me recent AI-related startup company"
    result = generate_response(test_query)
    print("\n--- LLM Response ---")
    print(result["answer"])
    print("\n--- Sources ---")
    print(result["sources"])
