from dotenv import load_dotenv
import os
import glob
import pickle
import requests
from bs4 import BeautifulSoup
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from PyPDF2 import PdfReader
load_dotenv()

# Global variables for the lovabot
model = None
embeddings = None
vector_store = None
text_splitter = None

def load_system_prompt():
    with open("ai/ai_lovabot/ai_lovabot_instructions.md", "r") as f:
        return f.read()

def init_ai():
    global model, embeddings, vector_store, text_splitter
    
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    
    # Initialize embeddings and vector store for RAG using OpenAI
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = InMemoryVectorStore(embeddings)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    return model

def scrape_website(url):
    """Scrape text content from a website URL"""
    try:
        print(f"Fetching content from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up extra whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        print(f"Successfully extracted {len(text)} characters from {url}")
        return text
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def add_dating_content():
    """Read all PDFs from data folder and scrape websites, then add to vector store and save embeddings"""
    global vector_store, text_splitter, embeddings
    
    if vector_store is None:
        init_ai()
    
    # Check if embeddings already exist
    embeddings_file = "ai/ai_lovabot/embeddings.pkl"
    if os.path.exists(embeddings_file):
        print("Loading existing embeddings...")
        load_embeddings()
        return {"message": "Loaded existing embeddings from file"}
    
    print("Processing PDFs and websites, creating embeddings...")
    
    all_documents = []
    
    # 1. Process PDF files
    pdf_files = glob.glob("ai/ai_lovabot/data/*.pdf")
    
    if pdf_files:
        print(f"\nProcessing {len(pdf_files)} PDF file(s)...")
        for pdf_file in pdf_files:
            print(f"Processing: {pdf_file}")
            try:
                # Read PDF content
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Create document
                doc = Document(
                    page_content=text,
                    metadata={"source": pdf_file, "type": "dating_article_pdf"}
                )
                all_documents.append(doc)
                
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
                continue
    else:
        print("No PDF files found in data folder")
    
    # 2. Process websites
    websites = [
        "https://theindependent.sg/21-of-singaporeans-cannot-accept-going-on-a-first-date-at-a-hawker-center-survey/",
        "https://www.traveloka.com/en-sg/explore/destination/romantic-places-in-singapore-acc/363645"
    ]
    
    print(f"\nProcessing {len(websites)} website(s)...")
    for url in websites:
        text = scrape_website(url)
        if text:
            # Create document
            doc = Document(
                page_content=text,
                metadata={"source": url, "type": "dating_article_web"}
            )
            all_documents.append(doc)
    
    if not all_documents:
        return {"message": "No documents could be processed"}
    
    # Split documents
    all_splits = text_splitter.split_documents(all_documents)
    
    # Add to vector store
    vector_store.add_documents(documents=all_splits)
    
    # Save embeddings to file (pass the documents directly)
    save_embeddings(all_splits)
    
    pdf_count = len(pdf_files) if pdf_files else 0
    web_count = len([d for d in all_documents if d.metadata.get("type") == "dating_article_web"])
    
    return {"message": f"Added {len(all_splits)} document chunks from {pdf_count} PDFs and {web_count} websites to vector store"}

def save_embeddings(documents=None):
    """Save vector store embeddings to file"""
    global vector_store, embeddings
    
    if documents is None:
        return
    
    # Create embeddings directory if it doesn't exist
    os.makedirs("ai/ai_lovabot", exist_ok=True)
    
    # Save documents and metadata
    documents_data = []
    for doc in documents:
        documents_data.append({
            'page_content': doc.page_content,
            'metadata': doc.metadata
        })
    
    with open("ai/ai_lovabot/embeddings.pkl", "wb") as f:
        pickle.dump(documents_data, f)
    
    print("Embeddings saved to ai/ai_lovabot/embeddings.pkl")

def load_embeddings():
    """Load vector store embeddings from file"""
    global vector_store, embeddings
    
    # Make sure embeddings model is initialized
    if embeddings is None:
        init_ai()
    
    embeddings_file = "ai/ai_lovabot/embeddings.pkl"
    if os.path.exists(embeddings_file):
        with open(embeddings_file, "rb") as f:
            documents_data = pickle.load(f)
        
        # Recreate documents and add to vector store
        documents = []
        for doc_data in documents_data:
            doc = Document(
                page_content=doc_data['page_content'],
                metadata=doc_data['metadata']
            )
            documents.append(doc)
        
        # Initialize vector store if needed
        if vector_store is None:
            vector_store = InMemoryVectorStore(embeddings)
        
        # Add documents to vector store
        vector_store.add_documents(documents)
        print("Embeddings loaded from file")
        return True
    return False

def chat(messages: list):
    """Chat function that uses RAG and conversation context"""
    global model, vector_store
    
    if model is None:
        init_ai()
    
    # Try to load existing embeddings if vector store is empty or None
    # Check if vector store has no documents by trying a test search
    needs_loading = False
    if vector_store is None:
        needs_loading = True
    else:
        # Test if vector store is empty by checking if it can retrieve anything
        try:
            test_results = vector_store.similarity_search("test", k=1)
            if len(test_results) == 0:
                needs_loading = True
        except:
            needs_loading = True
    
    if needs_loading:
        print("Loading embeddings...")
        load_embeddings()
    
    # Get the last user message (current question)
    current_question = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            current_question = msg.get("content", "")
            break
    
    if not current_question:
        return {"answer": "No user question found."}
    
    # Search for relevant context using RAG
    context = ""
    if vector_store is not None:
        retrieved_docs = vector_store.similarity_search(current_question)
        print(f"\nRAG Search Query: {current_question}")
        print(f"Retrieved {len(retrieved_docs)} documents")
        if retrieved_docs:
            for i, doc in enumerate(retrieved_docs):
                print(f"\n--- Document {i+1} (Source: {doc.metadata.get('source', 'unknown')}) ---")
                print(f"{doc.page_content[:200]}...")
            context = "\n\n".join(doc.page_content for doc in retrieved_docs)
        else:
            print("WARNING: No documents retrieved from vector store")
    
    # Load system prompt
    system_prompt = load_system_prompt()
    
    # Build conversation messages
    conversation_messages = [SystemMessage(content=system_prompt)]
    
    # Add context if available
    if context:
        conversation_messages.append(HumanMessage(content=f"Context from dating resources:\n{context}"))
    
    # Add conversation history
    for msg in messages:
        if msg.get("role") == "user":
            conversation_messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            conversation_messages.append(AIMessage(content=msg.get("content", "")))
    
    # Get AI response
    response = model.invoke(conversation_messages)
    return {"answer": response.content}