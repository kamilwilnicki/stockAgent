import urllib.parse
from mcp.server.fastmcp import FastMCP
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
import requests
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("simple-web-search-server")

@mcp.tool()
async def search_web(query: str) -> str:
    """Query the web engine for relevant links and websites
        Args:
        query: the query which will be used to search the web
    """
    api_key = os.getenv("SERPER_API_KEY")
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": 10
    }
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Format results for the agent
        formatted_results = f"Search results for: {query}\n\n"
        
        if "organic" in data:
            for i, item in enumerate(data["organic"][:5], 1):
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                formatted_results += f"{i}. **{title}**\n"
                formatted_results += f"   {snippet}\n"
                formatted_results += f"   Source: {link}\n\n"
        
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            formatted_results += f"\n**Key Information:**\n"
            if "description" in kg:
                formatted_results += f"{kg['description']}\n"
        
        return formatted_results if formatted_results else "No results found"
        
    except Exception as e:
        return f"Search failed: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")