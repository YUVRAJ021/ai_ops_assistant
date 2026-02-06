"""
GitHub Tool for AI Operations Assistant
Provides GitHub API integration for repository operations
"""

import requests
from typing import Dict, Any, Optional
from .base_tool import BaseTool


class GitHubTool(BaseTool):
    """Tool for interacting with GitHub API"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub tool
        
        Args:
            token: Optional GitHub personal access token for higher rate limits
        """
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Ops-Assistant"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    @property
    def name(self) -> str:
        return "github"
    
    @property
    def description(self) -> str:
        return "Search GitHub repositories, get repository details, stars, and descriptions"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search_repos", "get_repo", "get_user"],
                    "description": "Action to perform"
                },
                "query": {
                    "type": "string",
                    "description": "Search query for search_repos action"
                },
                "owner": {
                    "type": "string",
                    "description": "Repository owner for get_repo action"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name for get_repo action"
                },
                "username": {
                    "type": "string",
                    "description": "Username for get_user action"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute GitHub API action"""
        action = kwargs.get("action")
        
        try:
            if action == "search_repos":
                return self._search_repos(
                    query=kwargs.get("query", ""),
                    limit=kwargs.get("limit", 5)
                )
            elif action == "get_repo":
                return self._get_repo(
                    owner=kwargs.get("owner", ""),
                    repo=kwargs.get("repo", "")
                )
            elif action == "get_user":
                return self._get_user(username=kwargs.get("username", ""))
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    def _search_repos(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search GitHub repositories"""
        if not query:
            return {"success": False, "data": None, "error": "Query is required"}
        
        url = f"{self.BASE_URL}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        repos = []
        for item in data.get("items", []):
            repos.append({
                "name": item["name"],
                "full_name": item["full_name"],
                "description": item.get("description", "No description"),
                "stars": item["stargazers_count"],
                "forks": item["forks_count"],
                "language": item.get("language", "Unknown"),
                "url": item["html_url"],
                "owner": item["owner"]["login"]
            })
        
        return {
            "success": True,
            "data": {
                "total_count": data.get("total_count", 0),
                "repositories": repos
            },
            "error": None
        }
    
    def _get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository details"""
        if not owner or not repo:
            return {"success": False, "data": None, "error": "Owner and repo are required"}
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "data": {
                "name": data["name"],
                "full_name": data["full_name"],
                "description": data.get("description", "No description"),
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "watchers": data["watchers_count"],
                "language": data.get("language", "Unknown"),
                "url": data["html_url"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "topics": data.get("topics", []),
                "license": data.get("license", {}).get("name") if data.get("license") else None
            },
            "error": None
        }
    
    def _get_user(self, username: str) -> Dict[str, Any]:
        """Get GitHub user details"""
        if not username:
            return {"success": False, "data": None, "error": "Username is required"}
        
        url = f"{self.BASE_URL}/users/{username}"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "data": {
                "login": data["login"],
                "name": data.get("name", "N/A"),
                "bio": data.get("bio", "No bio"),
                "public_repos": data["public_repos"],
                "followers": data["followers"],
                "following": data["following"],
                "location": data.get("location", "Unknown"),
                "company": data.get("company", "N/A"),
                "blog": data.get("blog", ""),
                "url": data["html_url"],
                "created_at": data["created_at"]
            },
            "error": None
        }
