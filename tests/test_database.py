import os
import pytest
import sqlite3
from drawings_ai.database import DrawingsDatabase
from drawings_ai.schemas import DrawingSheet, EntityObject, ConfidenceLevel, IndexResult

@pytest.fixture
def temp_db_path(tmp_path):
    db_file = tmp_path / "test_drawings.db"
    return str(db_file)

def test_database_initialization(temp_db_path):
    db = DrawingsDatabase(temp_db_path)
    assert os.path.exists(temp_db_path)
    
    # Verify tables exist
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    assert "sheets" in tables
    assert "entities" in tables
    assert "dimensions" in tables

def test_database_save_and_append(temp_db_path):
    db = DrawingsDatabase(temp_db_path)
    
    sheet = DrawingSheet(sheet_number="S-101", title="Slab Layout", scale="1:100")
    entity = EntityObject(entity_type="slab", name="S1", material="Concrete", source_drawing_page="S-101", reliability=ConfidenceLevel.HIGH, count=1, dimensions={"thickness_mm": 200})
    result = IndexResult(drawing_sheets=[sheet], entities=[entity])
    
    # Save once
    db.save_index_result(result, append=False)
    summary = db.get_summary()
    assert summary["sheets_count"] == 1
    assert summary["entities_count"] == 1
    
    # Save another without append -> should overwrite
    sheet2 = DrawingSheet(sheet_number="E-201", title="Electrical Plan", scale="1:100")
    entity2 = EntityObject(entity_type="outlet", name="O1", material="Plastic", source_drawing_page="E-201", reliability=ConfidenceLevel.HIGH, count=1, dimensions={})
    result2 = IndexResult(drawing_sheets=[sheet2], entities=[entity2])
    
    db.save_index_result(result2, append=False)
    summary = db.get_summary()
    assert summary["sheets_count"] == 1
    assert summary["entities_count"] == 1
    assert "outlet" in summary["entities_breakdown"]
    assert "slab" not in summary["entities_breakdown"]
    
    # Save with append -> should aggregate
    db.save_index_result(result, append=True)
    summary = db.get_summary()
    assert summary["sheets_count"] == 2
    assert summary["entities_count"] == 2
    assert "outlet" in summary["entities_breakdown"]
    assert "slab" in summary["entities_breakdown"]

def test_query_security_validation(temp_db_path):
    db = DrawingsDatabase(temp_db_path)
    
    # Select should work
    res = db.execute_query("SELECT * FROM sheets")
    assert isinstance(res, list)
    if res:
        assert "error" not in res[0]
        
    # Write queries should fail
    bad_queries = [
        "DROP TABLE sheets",
        "DELETE FROM sheets",
        "INSERT INTO sheets (sheet_number) VALUES ('X-101')",
        "UPDATE sheets SET title = 'Hacked'",
        "CREATE TABLE test (id INTEGER)"
    ]
    for q in bad_queries:
        res = db.execute_query(q)
        assert "error" in res[0]
        assert "Security Access Violation" in res[0]["error"]
