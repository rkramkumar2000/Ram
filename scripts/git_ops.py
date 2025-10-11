#!/usr/bin/env python3
"""
Git operations module for managing SQL file versions using GitPython and PyGithub.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import List, Optional
from git import Repo, GitCommandError
from git.remote import Remote
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest

# Configure logging with file handler
LOG_FILE = 'logs/git_operations.log'
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Prevent propagation to root logger
logger.propagate = False

# Create handlers
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=1024*1024,  # 1MB
    backupCount=5,
    encoding='utf-8'
)
console_handler = logging.StreamHandler()

# Set levels
file_handler.setLevel(logging.DEBUG)
console_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s')
console_format = logging.Formatter('%(levelname)s - %(message)s')
file_handler.setFormatter(file_format)
console_handler.setFormatter(console_format)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Add a debug message to verify logger is working
logger.debug("Git operations logger initialized")
logger.info("Git operations module loaded")

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
        logger.debug(f"Initializing GitOps with repo_url={repo_url}, local_path={local_path}")
        self.repo_url = repo_url
        self.local_path = local_path
        self.repo: Optional[Repo] = None
        
        # Get GitHub token from environment
        logger.debug(f"Retrieving GitHub token from environment variable {github_token_env}")
        self.github_token = os.getenv(github_token_env)
        if not self.github_token:
            logger.error(f"GitHub token not found in environment variable {github_token_env}")
            raise GitError(f"GitHub token not found in environment variable {github_token_env}")
        
        # Initialize GitHub client
        logger.debug("Initializing GitHub client")
        self.github = Github(self.github_token)
        
        # Get repo name from URL if not provided
        if not repo_name:
            logger.debug("Extracting repo name from URL")
            # Extract owner/repo from HTTPS URL
            # Example: https://github.com/owner/repo.git -> owner/repo
            repo_name = repo_url.split('github.com/')[-1].replace('.git', '')
            logger.debug(f"Extracted repo name: {repo_name}")
        self.repo_name = repo_name
        
        try:
            logger.info(f"Attempting to access GitHub repository: {self.repo_name}")
            self.github_repo: Repository = self.github.get_repo(self.repo_name)
            logger.debug(f"Successfully accessed GitHub repository: {self.repo_name}")
        except Exception as e:
            logger.error(f"Failed to access GitHub repository {self.repo_name}: {str(e)}")
            raise GitError(f"Failed to access GitHub repository: {str(e)}")
            
        logger.info(f"Successfully initialized GitOps for repository {self.repo_name}")

    def clone_or_update_repo(self) -> None:
        """Clone repository if it doesn't exist, or pull latest changes if it does.
        
        Raises:
            GitError: If clone/pull operation fails
        """
        try:
            git_dir = os.path.join(self.local_path, '.git')
            if os.path.exists(git_dir):
                logger.info(f"Repository exists at {self.local_path}, updating...")
                logger.debug("Initializing existing repository")
                self.repo = Repo(self.local_path)
                
                # Ensure we have the correct remote URL
                logger.debug("Checking remote URL configuration")
                origin: Remote = self.repo.remote('origin')
                if origin.url != self.repo_url:
                    logger.info(f"Updating remote URL from {origin.url} to {self.repo_url}")
                    origin.set_url(self.repo_url)
                
                # Fetch and pull latest changes
                logger.debug("Fetching latest changes from remote")
                origin.fetch()
                logger.debug("Pulling latest changes from main branch")
                self.repo.git.pull('origin', 'main')
                logger.info("Repository updated successfully")
                logger.debug(f"Current commit hash: {self.repo.head.commit.hexsha}")
            else:
                logger.info(f"Repository does not exist, cloning to {self.local_path}")
                logger.debug(f"Cloning from {self.repo_url}")
                self.repo = Repo.clone_from(self.repo_url, self.local_path)
                logger.info("Repository cloned successfully")
                logger.debug(f"Cloned at commit: {self.repo.head.commit.hexsha}")
                
        except GitCommandError as e:
            logger.error(f"Git command failed: {str(e)}")
            logger.debug(f"Git error details: {e.stderr}")
            raise GitError(f"Git operation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during repository operation: {str(e)}")
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
            logger.debug(f"PR Details - Branch: {branch_name}, Base: {base}")
            logger.debug(f"PR Body: {body}")
            
            # Verify branch exists on remote
            logger.debug("Verifying branch exists on remote")
            remote_refs = [ref.name for ref in self.repo.remote().refs]
            if f'origin/{branch_name}' not in remote_refs:
                logger.warning(f"Branch {branch_name} not found on remote. Pushing branch first.")
                self.push_branch(branch_name)
            
            # Create pull request
            logger.debug("Creating pull request on GitHub")
            pr: PullRequest = self.github_repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=base
            )
            
            logger.info(f"Successfully created pull request: {pr.html_url}")
            logger.debug(f"PR number: {pr.number}")
            logger.debug(f"PR state: {pr.state}")
            return pr.html_url
            
        except Exception as e:
            logger.error(f"Failed to create pull request: {str(e)}")
            logger.debug(f"Error details: {repr(e)}")
            raise GitError(f"Failed to create pull request: {str(e)}")