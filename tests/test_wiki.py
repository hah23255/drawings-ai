import os
import pytest
from drawings_ai.wiki import DrawingsWiki

@pytest.fixture
def temp_wiki_dir(tmp_path):
    wiki_path = tmp_path / "wiki"
    return str(wiki_path)

def test_wiki_compilation(temp_wiki_dir):
    wiki = DrawingsWiki(temp_wiki_dir)
    
    sheets_text = {
        "S-101": "Slab details: concrete slump 80mm grade 32MPa",
        "E-201": "Electrical conduit cable tray runs"
    }
    
    index_path = wiki.compile_wiki(sheets_text)
    
    assert os.path.exists(index_path)
    assert os.path.exists(os.path.join(temp_wiki_dir, "concrete.md"))
    assert os.path.exists(os.path.join(temp_wiki_dir, "electrical.md"))
    
    # Read Page
    content = wiki.read_page("concrete")
    assert "Slab details" in content
    
    # Search Wiki
    res = wiki.search_wiki("conduit")
    assert len(res) == 1
    assert res[0]["page"] == "electrical.md"
    assert "conduit" in res[0]["snippet"]
