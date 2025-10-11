from git_ops import GitOps
import os

# Set up environment variable for testing
os.environ['GITHUB_TOKEN'] = 'test-token'

# Initialize GitOps (this will trigger our logging)
try:
    git = GitOps('https://github.com/rkramkumar2000/Ram.git', 'C:/Users/rkram/Downloads/SheetToSql')
except Exception as e:
    print(f"Error occurred: {e}")