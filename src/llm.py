from langchain_ollama import ChatOllama


MODEL_NAME = "llama3.2:latest"


def ask_llm(prompt):
    if not prompt or not prompt.strip():
        return "Please enter a question."

    llm = ChatOllama(
        model=MODEL_NAME,
        temperature=0.2,
    )

    response = llm.invoke(prompt)

    if hasattr(response, "content"):
        return response.content

    return str(response)