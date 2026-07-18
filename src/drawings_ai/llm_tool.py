from typing import Dict, List, Any, Optional
from drawings_ai.database import DrawingsDatabase
from drawings_ai.wiki import DrawingsWiki


class DrawingsAIToolKit:
    """
    Exposes a standardized toolkit of LLM-callable functions and JSON schemas
    compatible with OpenAI Tool Calling and Anthropic Claude Tools.
    """
    
    def __init__(self, db: DrawingsDatabase, wiki: DrawingsWiki):
        self.db = db
        self.wiki = wiki

    @staticmethod
    def get_tool_schemas() -> List[Dict[str, Any]]:
        """Returns the static JSON Schemas for the tools in the toolkit."""
        return [
            {
                "name": "query_drawings_database",
                "description": (
                    "Executes an SQL SELECT query against the structured relational drawings database (drawings.db). "
                    "Use this tool for quantity takeoffs, element counts (e.g., 'SELECT name, count FROM entities WHERE entity_type=\"footing\"'), "
                    "or structural measurements checks. Schema tables: "
                    "1) 'sheets' (sheet_number [PK], title, scale, revision); "
                    "2) 'entities' (id [PK], entity_type, name, material, source_drawing_page, reliability, count); "
                    "3) 'dimensions' (entity_id, dimension_key, dimension_value)."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "sql_query": {
                            "type": "STRING",
                            "description": "The exact SQLite SELECT query to execute, e.g., 'SELECT name, count, material FROM entities WHERE entity_type=\"footing\"'"
                        }
                    },
                    "required": ["sql_query"]
                }
            },
            {
                "name": "search_drawings_wiki",
                "description": "Searches the hierarchical markdown wiki text files (specs, code compliance, notes) for a keyword.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "The keyword or search query, e.g., 'concrete specification' or 'cable tray'"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "read_drawings_wiki_page",
                "description": (
                    "Reads the entire contents of a specific wiki page or the master register drawings index page. "
                    "Available pages: 'drawings' (for master index), 'concrete', 'electrical', 'structural_steel', 'general_notes'."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "page_name": {
                            "type": "STRING",
                            "description": "The page slug to read, e.g., 'concrete' or 'drawings'"
                        }
                    },
                    "required": ["page_name"]
                }
            },
            {
                "name": "get_drawing_sheets_metadata",
                "description": "Retrieves the register listing of all drawings, including sheet IDs, titles, scales, and revision stages.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Executes a tool with the provided arguments and returns a JSON-serializable result.
        """
        try:
            if tool_name == "query_drawings_database":
                sql = arguments.get("sql_query")
                if not sql:
                    return {"error": "Missing 'sql_query' argument."}
                return self.db.execute_query(sql)
                
            elif tool_name == "search_drawings_wiki":
                query = arguments.get("query")
                if not query:
                    return {"error": "Missing 'query' argument."}
                return self.wiki.search_wiki(query)
                
            elif tool_name == "read_drawings_wiki_page":
                page_name = arguments.get("page_name")
                if not page_name:
                    return {"error": "Missing 'page_name' argument."}
                # Handle 'drawings' special routing for the drawings.md index file
                if page_name.lower() == "drawings":
                    page_name = "drawings"
                return {"content": self.wiki.read_page(page_name)}
                
            elif tool_name == "get_drawing_sheets_metadata":
                return self.db.execute_query("SELECT * FROM sheets")
                
            else:
                return {"error": f"Tool '{tool_name}' not recognized in toolkit."}
                
        except Exception as e:
            return {"error": f"Execution error in tool '{tool_name}': {str(e)}"}
