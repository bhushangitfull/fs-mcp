import os
import json
from mcp.server.fastmcp import FastMCP
from smithery.decorators import smithery

@smithery.server()
def create_server():
    """Create and return a FastMCP server instance with filesystem tools."""
    
    server = FastMCP(name="filesystem-mcp-server")

    @server.tool()
    def read_file(path: str) -> str:
        """Read contents of a file.
        
        Args:
            path: Path to the file to read
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @server.tool()
    def write_file(path: str, content: str) -> str:
        """Write content to a file.
        
        Args:
            path: Path to the file to write
            content: Content to write to the file
        """
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    @server.tool()
    def list_directory(path: str = ".") -> str:
        """List contents of a directory.
        
        Args:
            path: Path to the directory (defaults to current directory)
        """
        try:
            items = os.listdir(path)
            return json.dumps(items, indent=2)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    @server.tool()
    def create_directory(path: str) -> str:
        """Create a new directory.
        
        Args:
            path: Path to the directory to create
        """
        try:
            os.makedirs(path, exist_ok=True)
            return f"Successfully created directory: {path}"
        except Exception as e:
            return f"Error creating directory: {str(e)}"

    @server.tool()
    def delete_file(path: str) -> str:
        """Delete a file.
        
        Args:
            path: Path to the file to delete
        """
        try:
            os.remove(path)
            return f"Successfully deleted: {path}"
        except Exception as e:
            return f"Error deleting file: {str(e)}"

    return server