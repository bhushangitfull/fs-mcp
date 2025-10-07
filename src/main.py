#!/usr/bin/env python3
import asyncio
import os
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

# Initialize MCP server
mcp = Server("filesystem-mcp-server")

@mcp.list_tools()
async def list_tools():
    """List available filesystem tools"""
    return [
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
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
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
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
                    "path": {"type": "string", "description": "Directory path", "default": "."}
                }
            }
        ),
        Tool(
            name="create_directory",
            description="Create a new directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to create"}
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
                    "path": {"type": "string", "description": "Path to delete"}
                },
                "required": ["path"]
            }
        )
    ]

@mcp.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool execution"""
    try:
        if name == "read_file":
            with open(arguments["path"], 'r', encoding='utf-8') as f:
                return [TextContent(type="text", text=f.read())]
        
        elif name == "write_file":
            with open(arguments["path"], 'w', encoding='utf-8') as f:
                f.write(arguments["content"])
            return [TextContent(type="text", text=f"Wrote to {arguments['path']}")]
        
        elif name == "list_directory":
            path = arguments.get("path", ".")
            items = os.listdir(path)
            return [TextContent(type="text", text=json.dumps(items, indent=2))]
        
        elif name == "create_directory":
            os.makedirs(arguments["path"], exist_ok=True)
            return [TextContent(type="text", text=f"Created {arguments['path']}")]
        
        elif name == "delete_file":
            os.remove(arguments["path"])
            return [TextContent(type="text", text=f"Deleted {arguments['path']}")]
        
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def handle_sse(request):
    """Handle SSE endpoint"""
    from mcp.server.sse import SseServerTransport
    from starlette.responses import StreamingResponse
    
    async with SseServerTransport("/messages") as transport:
        # Create async generators for communication
        async def read_stream():
            while True:
                message = await transport.reader.recv()
                yield message
        
        async def write_stream(generator):
            async for message in generator:
                await transport.writer.send(message)
        
        # Run the MCP server
        init_options = mcp.create_initialization_options()
        
        async def run_server():
            await mcp.run(
                transport.reader,
                transport.writer,
                init_options
            )
        
        # Start server and return SSE stream
        task = asyncio.create_task(run_server())
        
        async def event_generator():
            try:
                while not task.done():
                    await asyncio.sleep(0.1)
                    yield {"data": "heartbeat"}
            except Exception as e:
                print(f"Error in event generator: {e}")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )

async def handle_messages(request):
    """Handle messages POST endpoint"""
    from mcp.server.sse import SseServerTransport
    
    try:
        body = await request.json()
        print(f"Received message: {body}")
        
        # Process the MCP message
        # This is where the MCP protocol messages are handled
        
        return Response(
            content=json.dumps({"status": "ok"}),
            media_type="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        print(f"Error handling message: {e}")
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json"
        )

async def health_check(request):
    """Health check endpoint"""
    return Response(
        content=json.dumps({"status": "healthy", "server": "filesystem-mcp-server"}),
        media_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )

async def handle_options(request):
    """Handle CORS preflight"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", handle_sse, methods=["GET"]),
        Route("/messages", handle_messages, methods=["POST"]),
        Route("/messages", handle_options, methods=["OPTIONS"]),
        Route("/sse", handle_options, methods=["OPTIONS"]),
        Route("/health", health_check, methods=["GET"]),
    ]
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting MCP Filesystem Server")
    print(f"📍 SSE endpoint: http://{host}:{port}/sse")
    print(f"📬 Messages endpoint: http://{host}:{port}/messages")
    print(f"💚 Health check: http://{host}:{port}/health")
    
    uvicorn.run(app, host=host, port=port, log_level="info")