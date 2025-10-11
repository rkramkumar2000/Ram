"""Unit tests for Git operations."""

import pytest
import os
from unittest.mock import Mock, patch
from scripts.git_ops import GitOps, GitError
from git import Repo
from github import Github

@pytest.fixture
def mock_env(monkeypatch):
    """Fixture providing mock environment variables."""
    monkeypatch.setenv('GITHUB_TOKEN', 'test-token')
    return {'GITHUB_TOKEN': 'test-token'}

@pytest.fixture
def mock_repo(tmp_path):
    """Fixture providing a temporary Git repository."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    repo = Repo.init(str(repo_path))
    
    # Create initial commit
    (repo_path / "README.md").write_text("Test repo")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    
    return str(repo_path)

@pytest.fixture
def git_ops(mock_env, mock_repo):
    """Fixture providing a GitOps instance with mocked GitHub."""
    with patch('github.Github') as mock_github:
        # Mock the GitHub repository
        mock_repo = Mock()
        mock_repo.create_pull.return_value = Mock(html_url='https://github.com/test/test/pull/1')
        mock_github.return_value.get_repo.return_value = mock_repo
        
        ops = GitOps(
            repo_url="https://github.com/test/test.git",
            local_path=mock_repo,
            github_token_env='GITHUB_TOKEN',
            repo_name='test/test'
        )
        return ops

def test_initialization(mock_env):
    """Test GitOps initialization."""
    with patch('github.Github'):
        ops = GitOps(
            "https://github.com/test/test.git",
            "/tmp/test",
            'GITHUB_TOKEN',
            'test/test'
        )
        assert ops.repo_url == "https://github.com/test/test.git"
        assert ops.local_path == "/tmp/test"

def test_initialization_missing_token():
    """Test initialization with missing GitHub token."""
    with pytest.raises(GitError), patch('os.getenv', return_value=None):
        GitOps(
            "https://github.com/test/test.git",
            "/tmp/test",
            'MISSING_TOKEN',
            'test/test'
        )

def test_create_timestamped_branch(git_ops):
    """Test branch creation with timestamp."""
    git_ops.clone_or_update_repo()
    branch_name = git_ops.create_timestamped_branch('test-branch')
    
    assert branch_name.startswith('test-branch-')
    assert len(branch_name.split('-')) == 4  # prefix + date + time
    assert git_ops.repo.active_branch.name == branch_name

def test_add_and_commit(git_ops, tmp_path):
    """Test adding and committing files."""
    git_ops.clone_or_update_repo()
    
    # Create a test file
    test_file = tmp_path / "test.sql"
    test_file.write_text("CREATE TABLE test;")
    
    git_ops.add_and_commit([str(test_file)], "Test commit")
    
    # Verify commit
    latest_commit = git_ops.repo.head.commit
    assert "Test commit" in latest_commit.message
    assert any(str(test_file) in item.path for item in latest_commit.tree)

def test_push_branch_error_handling(git_ops):
    """Test error handling during branch push."""
    git_ops.clone_or_update_repo()
    branch_name = git_ops.create_timestamped_branch()
    
    # Mock a push error
    with patch('git.remote.Remote.push', side_effect=Exception("Push failed")):
        with pytest.raises(GitError) as exc_info:
            git_ops.push_branch(branch_name)
        assert "Push failed" in str(exc_info.value)

def test_create_pull_request(git_ops):
    """Test pull request creation."""
    pr_url = git_ops.create_pull_request(
        "test-branch",
        "Test PR",
        "Test description",
        "main"
    )
    
    assert pr_url == "https://github.com/test/test/pull/1"
    git_ops.github_repo.create_pull.assert_called_once_with(
        title="Test PR",
        body="Test description",
        head="test-branch",
        base="main"
    )

def test_clone_or_update_existing_repo(git_ops, mock_repo):
    """Test updating existing repository."""
    # First clone
    git_ops.clone_or_update_repo()
    
    # Create a change in the "remote"
    remote_repo = Repo(mock_repo)
    (Path(mock_repo) / "new_file.txt").write_text("new content")
    remote_repo.index.add(["new_file.txt"])
    remote_repo.index.commit("Remote change")
    
    # Update local repo
    git_ops.clone_or_update_repo()
    
    # Verify update
    assert os.path.exists(os.path.join(mock_repo, "new_file.txt"))

def test_error_handling_no_repo(git_ops):
    """Test operations requiring repository initialization."""
    with pytest.raises(GitError):
        git_ops.create_timestamped_branch()
    
    with pytest.raises(GitError):
        git_ops.add_and_commit(["test.sql"], "Test commit")
    
    with pytest.raises(GitError):
        git_ops.push_branch("test-branch")