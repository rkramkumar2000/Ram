# SheetSql

SheetSql is an automated tool that syncs Google Sheets data to SQL databases, using LLM-powered schema optimization and version control.

## Features
- Automated Google Sheets to SQL schema conversion
- LLM-powered SQL optimization and validation
- Automated Git versioning and PR creation
- GitHub Actions integration for scheduled syncs

## Setup

1. Clone the repository:
```bash
git clone https://github.com/rkramkumar2000/Ram.git
cd Ram
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Configure the following variables:
     - `GOOGLE_CREDENTIALS_FILE`: Path to Google Sheets API credentials
     - `SPREADSHEET_ID`: Your Google Spreadsheet ID
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `GITHUB_TOKEN`: GitHub personal access token
     - `GITHUB_REPO`: Repository in format "owner/repo"
     - Database configuration variables

4. Configure Google Sheets API:
   - Create a project in Google Cloud Console
   - Enable Google Sheets API
   - Create service account credentials
   - Share your spreadsheet with the service account email

## Usage

Run the schema sync manually:
```bash
python -m scripts.generate_sql
```

The tool will:
1. Read data from Google Sheets
2. Generate optimized SQL schema
3. Create SQL migration files
4. Commit changes and create a PR

## GitHub Actions

The repository includes a GitHub Action that runs the sync daily. To enable it:

1. Add required secrets to your GitHub repository
2. Configure the schedule in `.github/workflows/sql-sync.yml`

## Contributing

Pull requests are welcome! Please ensure tests pass before submitting.

## License

MIT
