import dotenv

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langchain_core.runnables import RunnablePassthrough
from langserve import add_routes

from langchain import hub
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

dotenv.load_dotenv()

app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple API server using LangChain's Runnable interfaces",
)

def get_rag_chain():
    loader = TextLoader("app/info.txt")
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, add_start_index=True)
    splits = text_splitter.split_documents(docs)      
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})

    prompt = hub.pull("rlm/rag-prompt")
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs if doc.page_content is not None)

@app.get("/")
async def root():
    return RedirectResponse(url="/chatbot/playground")
    
add_routes(
    app,
    get_rag_chain(),
    path="/chatbot",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
