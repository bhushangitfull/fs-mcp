from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
from sse_starlette import EventSourceResponse
import uvicorn
import os
import json
import asyncio

# Create MCP server
server = Server("filesystem-mcp-server")

# List available tools
@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory",
                        "default": "."
                    }
                }
            }
        ),
        Tool(
            name="create_directory",
            description="Create a new directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to create"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to delete"
                    }
                },
                "required": ["path"]
            }
        )
    ]

# Handle tool calls
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    try:
        if name == "read_file":
            path = arguments["path"]
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [TextContent(type="text", text=content)]
        
        elif name == "write_file":
            path = arguments["path"]
            content = arguments["content"]
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return [TextContent(type="text", text=f"Successfully wrote to {path}")]
        
        elif name == "list_directory":
            path = arguments.get("path", ".")
            items = os.listdir(path)
            result = json.dumps(items, indent=2)
            return [TextContent(type="text", text=result)]
        
        elif name == "create_directory":
            path = arguments["path"]
            os.makedirs(path, exist_ok=True)
            return [TextContent(type="text", text=f"Successfully created directory: {path}")]
        
        elif name == "delete_file":
            path = arguments["path"]
            os.remove(path)
            return [TextContent(type="text", text=f"Successfully deleted: {path}")]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# SSE endpoint handler
async def handle_sse(request):
    transport = SseServerTransport("/messages")
    
    async def run_server():
        async with transport.connect_sse(
            request.scope,
            request.receive,
            request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options()
            )
    
    return EventSourceResponse(
        run_server(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Health check endpoint
async def health(request):
    return Response(
        content='{"status": "healthy", "server": "filesystem-mcp-server"}',
        media_type="application/json"
    )

# Create Starlette app
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/health", endpoint=health),
    ]
)

# Run server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting MCP File System Server on {host}:{port}")
    print(f"SSE endpoint: http://{host}:{port}/sse")
    print(f"Health check: http://{host}:{port}/health")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )