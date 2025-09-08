# Database Chat Application

A standalone FastAPI application for natural language querying of PostgreSQL database using Gemini LLM.

## Features

- 🗃️ Natural language to SQL conversion
- 🤖 Powered by Google Gemini 1.5 Flash
- 📊 PostgreSQL database integration
- 🌐 Web-based chat interface
- 🔐 Runtime API key configuration
- 📋 Database schema introspection
- ✅ Query result formatting

## Setup

### 1. Environment Variables
Create a `.env` file with your database credentials:

```env
# Database Configuration
DB_USER=postgres
DB_PASS=ram
DB_HOST=localhost
DB_PORT=5432
DB_NAME=insurance_db
```

### 2. Database Schema
Ensure you have a `policies` table in your PostgreSQL database:

```sql
CREATE TABLE policies (
    policy_number VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100),
    status VARCHAR(20),
    pdf_path VARCHAR(255)
);
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python main.py
```

The application will start on `http://localhost:8001`

## Usage

1. Open your browser and navigate to `http://localhost:8001`
2. Enter your Gemini API key
3. Test the connection
4. Start asking questions about your policies in natural language

### Example Queries

- "Show me all active policies"
- "How many policies do we have in total?"
- "Find policies for customer John Smith"
- "Show me all pending policies"
- "What are the different policy statuses?"

## API Endpoints

- `GET /` - Web interface
- `POST /chat` - Chat with database
- `GET /health` - Health check
- `GET /schema` - Database schema information

## Technology Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **AI**: Google Gemini 1.5 Flash
- **Frontend**: HTML/JavaScript
- **Environment**: Python 3.8+

## Configuration

The application runs on port 8001 by default. You can modify this in the `main.py` file:

```python
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
```
