from langchain_groq import ChatGroq

PROMPT_TEMPLATE = """You are a helpful AI assistant.
Answer ONLY using the context below.
If the answer is not present, reply exactly:
"The answer is not available on the provided website."

Context:
{context}

Conversation History:
{history}

Question:
{question}

Answer:
"""

class SimpleMemory:
    def __init__(self):
        self.history = []

    def save_context(self, inputs: dict, outputs: dict) -> None:
        self.history.append(f"User: {inputs['question']}")
        self.history.append(f"Assistant: {outputs['answer']}")

    def load(self) -> str:
        return "\n".join(self.history)

class SimpleRAGChain:
    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever
        self.memory = SimpleMemory()

    def invoke(self, inputs: dict) -> dict:
        question = inputs["question"]
        docs = self.retriever.invoke(question)
        
        if not docs:
            return {"answer": "The answer is not available on the provided website.", "source_documents": []}
        
        context = "\n\n".join(d.page_content for d in docs)
        prompt = PROMPT_TEMPLATE.format(
            context=context,
            history=self.memory.load(),
            question=question
        )
        answer = self.llm.invoke(prompt).content
        self.memory.save_context({"question": question}, {"answer": answer})
        
        return {"answer": answer, "source_documents": docs}

def setup_qa_chain(vectorstore, groq_api_key):
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0, groq_api_key=groq_api_key)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    return SimpleRAGChain(llm, retriever)

def ask_question(chain, question: str) -> str:
    return chain.invoke({"question": question})["answer"]
