// Google Apps Script to send webhook notifications on sheet edits

// Properties to store webhook configuration
const SCRIPT_PROPERTIES = PropertiesService.getScriptProperties();

/**
 * Triggered when any cell in the spreadsheet is edited
 */
function onEdit(e) {
  // Get active sheet and edited range
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  
  // Get editor info and timestamp
  const editor = Session.getActiveUser().getEmail();
  const timestamp = new Date().toISOString();
  
  // Prepare payload
  const payload = {
    sheetId: e.source.getId(),
    sheetName: sheet.getName(),
    lastEditor: editor,
    timestamp: timestamp,
    changedRange: {
      a1Notation: range.getA1Notation(),
      startRow: range.getRow(),
      startCol: range.getColumn(),
      numRows: range.getNumRows(),
      numCols: range.getNumColumns(),
      values: range.getValues()
    }
  };

  // Send webhook if configured
  sendWebhook(payload);
}

/**
 * Send payload to configured webhook URL
 */
function sendWebhook(payload) {
  const webhookUrl = SCRIPT_PROPERTIES.getProperty('WEBHOOK_URL');
  if (!webhookUrl) {
    console.log('Webhook URL not configured');
    return;
  }

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  };

  try {
    UrlFetchApp.fetch(webhookUrl, options);
  } catch (error) {
    console.error('Failed to send webhook:', error);
  }
}

/**
 * Configure webhook URL via WebApp UI
 */
function doGet() {
  const template = HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
      <head>
        <base target="_top">
        <title>Webhook Configuration</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          .form-group { margin-bottom: 15px; }
          input[type="text"] { width: 100%; padding: 8px; margin-top: 5px; }
          button { padding: 10px 20px; background: #4285f4; color: white; border: none; cursor: pointer; }
          .success { color: green; margin-top: 10px; }
          .error { color: red; margin-top: 10px; }
        </style>
      </head>
      <body>
        <h2>Configure Webhook URL</h2>
        <div class="form-group">
          <label for="webhookUrl">Webhook URL:</label><br>
          <input type="text" id="webhookUrl" value="${SCRIPT_PROPERTIES.getProperty('WEBHOOK_URL') || ''}" />
        </div>
        <button onclick="saveWebhook()">Save</button>
        <div id="status"></div>
        
        <script>
          function saveWebhook() {
            const url = document.getElementById('webhookUrl').value;
            google.script.run
              .withSuccessHandler(onSuccess)
              .withFailureHandler(onError)
              .saveWebhookUrl(url);
          }
          
          function onSuccess() {
            document.getElementById('status').innerHTML = '<p class="success">Webhook URL saved successfully!</p>';
          }
          
          function onError(error) {
            document.getElementById('status').innerHTML = '<p class="error">Error saving webhook URL: ' + error + '</p>';
          }
        </script>
      </body>
    </html>
  `);
  
  return template;
}

/**
 * Save webhook URL to script properties
 */
function saveWebhookUrl(url) {
  SCRIPT_PROPERTIES.setProperty('WEBHOOK_URL', url);
}