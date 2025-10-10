#!/usr/bin/env python3
"""
Git operations module for managing SQL file versions using GitPython and PyGithub.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional
from git import Repo, GitCommandError
from git.remote import Remote
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitError(Exception):
    """Base exception for git operations."""
    pass

class GitOps:
    """Manages Git operations for SQL schema version control."""
    
    def __init__(
        self,
        repo_url: str,
        local_path: str,
        github_token_env: str = 'GITHUB_TOKEN',
        repo_name: str = None
    ):
        """Initialize GitOps with repository details.
        
        Args:
            repo_url: HTTPS URL of the Git repository
            local_path: Local path where repository should be cloned
            github_token_env: Environment variable name containing GitHub token
            repo_name: GitHub repository name in format 'owner/repo'
        
        Raises:
            GitError: If GitHub token is not found in environment
        """
        self.repo_url = repo_url
        self.local_path = local_path
        self.repo: Optional[Repo] = None
        
        # Get GitHub token from environment
        self.github_token = os.getenv(github_token_env)
        if not self.github_token:
            raise GitError(f"GitHub token not found in environment variable {github_token_env}")
        
        # Initialize GitHub client
        self.github = Github(self.github_token)
        
        # Get repo name from URL if not provided
        if not repo_name:
            # Extract owner/repo from HTTPS URL
            # Example: https://github.com/owner/repo.git -> owner/repo
            repo_name = repo_url.split('github.com/')[-1].replace('.git', '')
        self.repo_name = repo_name
        
        try:
            self.github_repo: Repository = self.github.get_repo(self.repo_name)
        except Exception as e:
            raise GitError(f"Failed to access GitHub repository: {str(e)}")
            
        logger.info(f"Initialized GitOps for repository {self.repo_name}")

    def clone_or_update_repo(self) -> None:
        """Clone repository if it doesn't exist, or pull latest changes if it does.
        
        Raises:
            GitError: If clone/pull operation fails
        """
        try:
            if os.path.exists(os.path.join(self.local_path, '.git')):
                logger.info("Repository exists, updating...")
                self.repo = Repo(self.local_path)
                
                # Ensure we have the correct remote URL
                origin: Remote = self.repo.remote('origin')
                if origin.url != self.repo_url:
                    origin.set_url(self.repo_url)
                
                # Fetch and pull latest changes
                origin.fetch()
                self.repo.git.pull('origin', 'main')
                logger.info("Repository updated successfully")
            else:
                logger.info(f"Cloning repository to {self.local_path}")
                self.repo = Repo.clone_from(self.repo_url, self.local_path)
                logger.info("Repository cloned successfully")
                
        except GitCommandError as e:
            raise GitError(f"Git operation failed: {str(e)}")
        except Exception as e:
            raise GitError(f"Repository operation failed: {str(e)}")

    def create_timestamped_branch(self, prefix: str = 'sql-update') -> str:
        """Create a new branch with timestamp suffix.
        
        Args:
            prefix: Prefix for the branch name
            
        Returns:
            str: Name of created branch
            
        Raises:
            GitError: If branch creation fails
        """
        if not self.repo:
            raise GitError("Repository not initialized. Call clone_or_update_repo first.")
            
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"{prefix}-{timestamp}"
        
        try:
            current = self.repo.active_branch
            logger.info(f"Creating new branch {branch_name} from {current.name}")
            
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            
            logger.info(f"Created and checked out branch {branch_name}")
            return branch_name
            
        except Exception as e:
            raise GitError(f"Failed to create branch: {str(e)}")

    def add_and_commit(self, files: List[str], commit_message: str) -> None:
        """Stage and commit specified files.
        
        Args:
            files: List of file paths to commit
            commit_message: Commit message
            
        Raises:
            GitError: If commit operation fails
        """
        if not self.repo:
            raise GitError("Repository not initialized. Call clone_or_update_repo first.")
            
        try:
            # Validate files exist
            for file in files:
                if not os.path.exists(file):
                    raise GitError(f"File not found: {file}")
            
            # Add files to staging area
            self.repo.index.add(files)
            
            # Create commit
            self.repo.index.commit(commit_message)
            logger.info(f"Committed {len(files)} files: {commit_message}")
            
        except Exception as e:
            raise GitError(f"Failed to commit changes: {str(e)}")

    def push_branch(self, branch_name: str) -> None:
        """Push branch to remote repository.
        
        Args:
            branch_name: Name of branch to push
            
        Raises:
            GitError: If push operation fails
        """
        if not self.repo:
            raise GitError("Repository not initialized. Call clone_or_update_repo first.")
            
        try:
            logger.info(f"Pushing branch {branch_name} to origin")
            origin: Remote = self.repo.remote('origin')
            
            # Add token to URL for authentication
            origin.set_url(self.repo_url.replace(
                "https://",
                f"https://{self.github_token}@"
            ))
            
            # Push branch
            origin.push(branch_name)
            logger.info(f"Successfully pushed branch {branch_name}")
            
        except Exception as e:
            raise GitError(f"Failed to push branch: {str(e)}")
        finally:
            # Reset URL to remove token
            origin.set_url(self.repo_url)

    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
        base: str = 'main'
    ) -> str:
        """Create a pull request on GitHub.
        
        Args:
            branch_name: Name of branch containing changes
            title: PR title
            body: PR description
            base: Base branch to merge into
            
        Returns:
            str: URL of created pull request
            
        Raises:
            GitError: If PR creation fails
        """
        try:
            logger.info(f"Creating pull request: {title}")
            
            pr: PullRequest = self.github_repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=base
            )
            
            logger.info(f"Created pull request: {pr.html_url}")
            return pr.html_url
            
        except Exception as e:
            raise GitError(f"Failed to create pull request: {str(e)}")