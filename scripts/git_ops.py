#!/usr/bin/env python3
"""
Git operations module for managing SQL file versions.
"""

from git import Repo
from github import Github
import os
from typing import List

class GitOps:
    def __init__(self, repo_path: str, github_token: str = None):
        """Initialize Git operations."""
        self.repo = Repo(repo_path)
        if github_token:
            self.github = Github(github_token)
        else:
            self.github = Github(os.getenv('GITHUB_TOKEN'))

    def commit_sql_changes(self, files: List[str], message: str) -> bool:
        """Commit SQL file changes to the repository."""
        try:
            # Stage files
            for file in files:
                self.repo.index.add(file)
            
            # Create commit
            self.repo.index.commit(message)
            return True
        except Exception as e:
            print(f"Error committing changes: {str(e)}")
            return False

    def create_pull_request(self, branch_name: str, title: str, body: str) -> bool:
        """Create a pull request for SQL changes."""
        try:
            # Push changes
            origin = self.repo.remote('origin')
            origin.push(branch_name)

            # Create PR
            repo_name = os.getenv('GITHUB_REPO')
            gh_repo = self.github.get_repo(repo_name)
            gh_repo.create_pull(
                title=title,
                body=body,
                base='main',
                head=branch_name
            )
            return True
        except Exception as e:
            print(f"Error creating pull request: {str(e)}")
            return False