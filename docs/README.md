# Policy RAG Chat Application

A FastAPI-based Retrieval-Augmented Generation (RAG) application that allows you to chat with PDF documents using Google's Gemini LLM.

## Features

- 📄 PDF document processing and indexing
- 🤖 Chat interface powered by Google Gemini
- 🔍 Semantic search through document content
- 💾 Vector database storage with FAISS
- 🌐 Web-based chat interface
- 🔐 Secure API key handling

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key (get it from [Google AI Studio](https://makersuite.google.com/))

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd c:\Users\rkram\OneDrive\Desktop\policy_rag_app
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify your PDF file exists:**
   Make sure your PDF file is located at: `C:\Users\rkram\Downloads\sample_policy_info_text.pdf`

### Running the Application

1. **Start the FastAPI server:**
   ```bash
   python main.py
   ```
   
   Or alternatively:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the application:**
   Open your web browser and go to: `http://localhost:8000`

3. **Enter your API key:**
   - In the web interface, enter your Google Gemini API key in the input field
   - Start asking questions about your policy document!

### API Endpoints

- `GET /` - Web chat interface
- `POST /chat` - Chat API endpoint
- `GET /health` - Health check endpoint

### Example Chat Request

```json
{
  "message": "What are the key policies mentioned in this document?",
  "api_key": "your_gemini_api_key_here"
}
```

### Example Response

```json
{
  "response": "Based on the document, the key policies include...",
  "sources": [
    {
      "chunk_id": 0,
      "content": "Relevant text excerpt from the document..."
    }
  ]
}
```

## Project Structure

```
policy_rag_app/
├── main.py              # FastAPI application
├── rag_system.py        # RAG implementation
├── requirements.txt     # Python dependencies
├── .env                # Environment variables
├── static/
│   └── index.html      # Web chat interface
└── vectorstore/        # Generated vector database (after first run)
```

## How It Works

1. **Document Processing**: The PDF is loaded and split into chunks
2. **Vector Indexing**: Text chunks are converted to embeddings using sentence-transformers
3. **Storage**: Embeddings are stored in a FAISS vector database
4. **Query Processing**: User questions are embedded and similar chunks are retrieved
5. **Response Generation**: Gemini LLM generates answers based on retrieved context

## Troubleshooting

- **PDF not found**: Ensure the PDF file exists at the specified path
- **API key errors**: Verify your Gemini API key is valid and has sufficient quota
- **Package installation issues**: Try using `pip install --upgrade pip` first
- **Port already in use**: Change the port in `main.py` or kill the process using port 8000

## Security Notes

- API keys are only used for the current session
- No API keys are stored on the server
- Use environment variables for production deployments

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key and paste it in the web interface

Enjoy chatting with your policy documents! 🚀
