import sqlite3
import re
from typing import List, Dict, Any, Tuple
from drawings_ai.schemas import DrawingSheet, EntityObject, ConfidenceLevel, IndexResult


class DrawingsDatabase:
    """
    Manages the SQLite database (drawings.db) for physical building elements.
    Includes support for multi-drawing aggregation (append mode) and 
    read-only query security validation.
    """
    
    def __init__(self, db_path: str = "drawings.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes tables for sheets, physical entities, and dimensions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sheets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sheets (
                sheet_number TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                scale TEXT,
                revision TEXT DEFAULT 'A'
            )
        """)
        
        # Create entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                material TEXT,
                source_drawing_page TEXT,
                reliability TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                FOREIGN KEY(source_drawing_page) REFERENCES sheets(sheet_number) ON DELETE CASCADE
            )
        """)
        
        # Create dimensions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dimensions (
                entity_id INTEGER,
                dimension_key TEXT NOT NULL,
                dimension_value REAL NOT NULL,
                PRIMARY KEY (entity_id, dimension_key),
                FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()

    def save_index_result(self, result: IndexResult, append: bool = False):
        """
        Persists index sheets and entities to the database.
        If append=False, existing data in the database is wiped.
        If append=True, records are inserted or replaced, allowing multi-file aggregation.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if not append:
            # Clear existing tables
            cursor.execute("DELETE FROM dimensions")
            cursor.execute("DELETE FROM entities")
            cursor.execute("DELETE FROM sheets")
            
        # Insert sheets
        for sheet in result.drawing_sheets:
            cursor.execute("""
                INSERT OR REPLACE INTO sheets (sheet_number, title, scale, revision) 
                VALUES (?, ?, ?, ?)
            """, (sheet.sheet_number, sheet.title, sheet.scale, sheet.revision))
            
        # Insert entities and dimensions
        for entity in result.entities:
            # Check if this exact entity already exists on the same page
            if append:
                cursor.execute("""
                    SELECT id FROM entities 
                    WHERE entity_type = ? AND name = ? AND source_drawing_page = ?
                """, (entity.entity_type, entity.name, entity.source_drawing_page))
                row = cursor.fetchone()
                if row:
                    # Update count and skip duplicate insertion
                    cursor.execute("""
                        UPDATE entities SET count = count + ? WHERE id = ?
                    """, (entity.count, row[0]))
                    continue
                    
            cursor.execute("""
                INSERT INTO entities (entity_type, name, material, source_drawing_page, reliability, count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (entity.entity_type, entity.name, entity.material, entity.source_drawing_page, entity.reliability.value, entity.count))
            
            entity_id = cursor.lastrowid
            
            for dim_key, dim_val in entity.dimensions.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO dimensions (entity_id, dimension_key, dimension_value) 
                    VALUES (?, ?, ?)
                """, (entity_id, dim_key, dim_val))
                
        conn.commit()
        conn.close()

    def execute_query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Executes an SQL query against the drawings schema.
        Secures database integrity by rejecting write queries (DROP, INSERT, UPDATE, DELETE).
        """
        # Security check: Block modifying queries
        sql_clean = sql.strip().upper()
        blacklisted_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "REPLACE", "TRUNCATE"]
        if any(re.search(rf'\b{kw}\b', sql_clean) for kw in blacklisted_keywords):
            return [{"error": "Security Access Violation: Write operations are not permitted on this query interface."}]
            
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        except Exception as e:
            result = [{"error": str(e)}]
        finally:
            conn.close()
            
        return result

    def get_summary(self) -> Dict[str, Any]:
        """Provides aggregates from the relational database."""
        sheets_count = self.execute_query("SELECT COUNT(*) as count FROM sheets")[0].get("count", 0)
        entities_count = self.execute_query("SELECT COUNT(*) as count FROM entities")[0].get("count", 0)
        
        entity_types = self.execute_query(
            "SELECT entity_type, SUM(count) as total FROM entities GROUP BY entity_type"
        )
        
        breakdown = {}
        for row in entity_types:
            if "entity_type" in row:
                breakdown[row["entity_type"]] = row["total"]
                
        return {
            "sheets_count": sheets_count,
            "entities_count": entities_count,
            "entities_breakdown": breakdown
        }
