from typing import List, Dict, Any
import json
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
    if isinstance(retrieved_results, list) and retrieved_results:
        # Pass raw JSON to save tokens and provide structured data
        context_str = json.dumps(retrieved_results, ensure_ascii=False)
    else:
        context_str = "No specific documents found."

    system_prompt = """You are Transcout AI, a helpful and direct assistant for a tech knowledge graph.
    
    Guidelines:
    1. **Direct Address**: Always address the user directly as "you". Never refer to them as "the user".
    2. **Context-Based**: Answer questions based ONLY on the provided retrieved tickets/documents (in JSON format).
    3. **No Data Handling**: If the provided context is empty or "No specific documents found.", politely inform the user that you couldn't find any relevant information in the database. Suggest they try broader keywords or different locations/sources.
    4. **Citations**: Cite your sources by referring to the 'rank' or 'title' when appropriate.
    5. **Tone**: Be professional, concise, and helpful.
    Use all 5 record data to answer the user's query. Not just the top 1 record.
    You dont have to tell the ranking number of the record.
    Also tell the user the source of the record.
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
