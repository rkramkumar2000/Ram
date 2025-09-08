from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from pypdf import PdfReader
import google.generativeai as genai
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import os
import pickle
import sys
from pathlib import Path

# Add parent directories to path to find config
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import VECTORSTORE_DIR

class RAGSystem:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.vectorstore = None
        self.model = None  # Gemini model (backup)
        self.groq_model = None  # Primary Groq model
        self.documents = []
        
    def load_document(self, pdf_path: str):
        """Load and process PDF document"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        # Extract text from PDF
        pdf_reader = PdfReader(pdf_path)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
            
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF")
            
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create vector store
        self.vectorstore = FAISS.from_texts(
            texts=chunks,
            embedding=self.embeddings
        )
        
        # Save vectorstore for future use
        self.vectorstore.save_local(str(VECTORSTORE_DIR))
        
        print(f"Successfully processed PDF into {len(chunks)} chunks")
        
    def load_vectorstore(self):
        """Load existing vectorstore if available"""
        if os.path.exists(str(VECTORSTORE_DIR)):
            self.vectorstore = FAISS.load_local(
                str(VECTORSTORE_DIR),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            return True
        return False
        
    def setup_model(self, api_key: str):
        """Setup the Groq model (primary) and Gemini model (backup)"""
        if not self.vectorstore:
            if not self.load_vectorstore():
                raise ValueError("No vectorstore available. Please load a document first.")
        
        print(f"Setting up models with API key: {api_key[:10]}...")
        
        # First, try to setup Groq model (primary)
        try:
            if api_key.startswith('gsk_'):
                print("[i] Detected Groq API key, setting up Groq model...")
                self.groq_model = ChatGroq(
                    groq_api_key=api_key,
                    model_name="llama3-70b-8192",
                    temperature=0.1
                )
                print("[+] Groq model configured for RAG")
            else:
                print("[i] Non-Groq API key, setting up Gemini model...")
                genai.configure(api_key=api_key.strip())
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                print("[+] Gemini model configured for RAG")
                
        except Exception as e:
            print(f"[x] Error in setup_model: {e}")
            raise
        
    def get_relevant_context(self, question: str, k: int = 3) -> list:
        """Retrieve relevant document chunks"""
        if not self.vectorstore:
            return []
            
        docs = self.vectorstore.similarity_search(question, k=k)
        return [doc.page_content for doc in docs]
        
    def query_with_key(self, question: str, api_key: str) -> dict:
        """Query the RAG system with runtime API key"""
        if not api_key:
            raise ValueError("API key is required")
            
        print(f"Using runtime API key: {api_key[:10]}... (length: {len(api_key)})")
            
        # Setup model with the provided API key
        self.setup_model(api_key)
            
        # Get relevant context
        context_chunks = self.get_relevant_context(question)
        context = "\n\n".join(context_chunks)
        
        # Create prompt
        prompt = f"""You are a helpful assistant that answers questions about policy documents. 
Use the following pieces of context to answer the question at the end. 
If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}

Answer: """
        
        # Generate response
        try:
            if self.groq_model:
                print(f"🧠 Using Groq for RAG response generation...")
                messages = [
                    SystemMessage(content="You are a helpful assistant that answers questions about policy documents. Use the provided context to give accurate, detailed answers."),
                    HumanMessage(content=prompt)
                ]
                response = self.groq_model.invoke(messages)
                answer = response.content
                print(f"[+] Got response from Groq: {len(answer)} characters")
            else:
                print(f"🧠 Using Gemini for RAG response generation...")
                print(f"Prompt length: {len(prompt)} characters")
                response = self.model.generate_content(prompt)
                answer = response.text
                print(f"[+] Got response from Gemini: {len(answer)} characters")
                
        except Exception as e:
            print(f"[x] LLM API Error: {str(e)}")
            raise ValueError(f"Error generating response: {str(e)}")
        
        # Prepare sources
        sources = []
        for i, chunk in enumerate(context_chunks):
            sources.append({
                "chunk_id": i,
                "content": chunk[:200] + "..." if len(chunk) > 200 else chunk
            })
                
        return {
            "answer": answer,
            "sources": sources
        }

    def query(self, question: str) -> dict:
        """Query the RAG system with environment API key"""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("API key not found in environment variables")
            
        return self.query_with_key(question, api_key)
