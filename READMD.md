# ABOUT

This documents the steps to build an MCP Server that:
- Connects to my company's PostgreSQL database
- Exposes table schemas as resources
- Provides tools for running read-only SQL queries
- Includes prompts for common data analysis tasks

This use case is derived from the tutorial on [Building MCP with LLMs](https://modelcontextprotocol.io/tutorials/building-mcp-with-llms) using ChatGPT as the LLM.

## Step to buildong an MCP Server

(the purpose of the MCP Server is as mentioned in the main [ABOUT](#about) section.)

1. Install dependencies
```bash
pip install "mcp[cli]" asyncpg psycopg
```

2. Create the MCP server (`server.py`)
```python
import asyncpg
from mcp.server.fastmcp import FastMCP, Context

# Create the server
mcp = FastMCP("Postgres MCP Server")

# Database config (replace with your actual settings or load from .env)
DB_URL = "postgresql://user:password@host:port/database"

# --- LIFESPAN: Connect on startup ---
@mcp.lifespan()
async def connect_db():
    conn = await asyncpg.connect(DB_URL)
    yield {"db": conn}
    await conn.close()

# --- RESOURCES: Expose list of table schemas ---
@mcp.resource("pgschema://{table}")
async def get_table_schema(ctx: Context, table: str) -> str:
    db = ctx.request_context.lifespan_context["db"]
    result = await db.fetch(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = $1
    """, table)
    return "\n".join(f"{row['column_name']} ({row['data_type']})" for row in result)

# --- TOOL: Run a safe, read-only SQL query ---
@mcp.tool()
async def run_sql(query: str, ctx: Context) -> str:
    if not query.strip().lower().startswith("select"):
        return "Only SELECT queries are allowed."
    db = ctx.request_context.lifespan_context["db"]
    try:
        rows = await db.fetch(query)
        return "\n".join(str(dict(r)) for r in rows)
    except Exception as e:
        return f"Error: {e}"

# --- PROMPTS: Reusable data analysis tasks ---
@mcp.prompt()
def summarize_table(table: str) -> str:
    return f"What are the most important insights in the `{table}` table?"

@mcp.prompt()
def find_trends(column: str, table: str) -> str:
    return f"Are there any patterns or trends in `{column}` from the `{table}` table?"
```

3. Run the server locally
```bash
mcp dev server.py
```

4. Use with Claude Desktop or any MCP client
```bash
mcp install server.py --name "Company DB Explorer"
```
