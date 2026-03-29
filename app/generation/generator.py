from langchain_openai.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def generate_answer(context, query):
    prompt=f"""
    Answer the question using only the context below.
    Context : {context}
    Question : {query}
    """

    response = llm.invoke(prompt)
    return response.content