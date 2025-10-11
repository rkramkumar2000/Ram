# Sheet Edit Webhook Setup

## Google Apps Script Deployment

1. Open your Google Sheet
2. Go to Extensions > Apps Script
3. Create a new script and paste the contents of `sheet_scripts/webhook_notifier.gs`
4. Deploy as Web App:
   - Click "Deploy" > "New deployment"
   - Select "Web app"
   - Set the following:
     - Execute as: "Me"
     - Who has access: "Anyone"
   - Click "Deploy"
   - Authorize the app when prompted

5. Configure Webhook URL:
   - After deployment, copy the Web App URL
   - Open the Web App URL in your browser
   - Enter your webhook receiver URL
   - Click "Save"

## Local Webhook Receiver (Development)

1. Install dependencies:
   ```bash
   pip install flask
   ```

2. Set environment variables:
   ```bash
   # Windows PowerShell
   $env:REPO_PATH = "C:\path\to\sheettosql"
   $env:PYTHON_PATH = "python"
   ```

3. Run the Flask app:
   ```bash
   cd webhook_receiver
   python app.py
   ```

4. Make your webhook receiver accessible:
   - For development, use tools like ngrok:
     ```bash
     ngrok http 5000
     ```
   - Copy the HTTPS URL and configure it in the Google Apps Script Web App

## Production Deployment

For production, consider:

1. Using a proper WSGI server (e.g., gunicorn)
2. Setting up HTTPS
3. Adding authentication to the webhook endpoint
4. Using environment variables for configuration
5. Setting up logging
6. Implementing retry mechanisms

## Testing the Webhook

Test curl command:
```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sheetId": "your-sheet-id",
    "sheetName": "Sheet1",
    "lastEditor": "user@example.com",
    "timestamp": "2025-10-10T12:00:00Z",
    "changedRange": {
      "a1Notation": "A1:B2",
      "startRow": 1,
      "startCol": 1,
      "numRows": 2,
      "numCols": 2,
      "values": [["test", "data"]]
    }
  }'
```