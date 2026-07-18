import os
import pytest
from drawings_ai.pipeline import DrawingsAIPipeline

@pytest.fixture
def temp_workspace(tmp_path):
    return str(tmp_path)

def test_pipeline_integration(temp_workspace):
    pipeline = DrawingsAIPipeline(workspace_dir=temp_workspace)
    
    # Use mock parsing by passing mock.pdf path
    res = pipeline.index_drawings("mock.pdf", append=False)
    
    assert len(res.drawing_sheets) == 3
    assert len(res.entities) == 3
    
    db_path = os.path.join(temp_workspace, "drawings.db")
    assert os.path.exists(db_path)
    
    wiki_index = os.path.join(temp_workspace, "drawings.md")
    assert os.path.exists(wiki_index)
    
    # Check toolkit
    toolkit = pipeline.get_toolkit()
    schemas = toolkit.get_tool_schemas()
    assert len(schemas) == 4
    
    # Run tool query
    db_res = toolkit.execute_tool("query_drawings_database", {"sql_query": "SELECT COUNT(*) as count FROM sheets"})
    assert db_res[0]["count"] == 3
