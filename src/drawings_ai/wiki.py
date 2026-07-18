import os
import re
from typing import Dict, List, Any


class DrawingsWiki:
    """
    Compiles and manages non-visual text-based specification drawing data
    into a structured hierarchical Markdown Wiki.
    Based on Andre Karpathy's LLM Wiki structure, enabling low-token keyword lookup.
    """
    
    def __init__(self, wiki_dir: str = "wiki"):
        self.wiki_dir = wiki_dir
        os.makedirs(self.wiki_dir, exist_ok=True)
        
        # Default trades keyword mapping
        self.categories = {
            "concrete": ["concrete", "cement", "slab", "footing", "rebar", "reinforcement", "mpa", "slump"],
            "electrical": ["electrical", "conduit", "cable", "tray", "wire", "lighting", "circuit", "panel", "socket", "outlet"],
            "structural_steel": ["steel", "structural steel", "beam", "column", "w-shape", "bolt", "weld", "grade 50", "hand rail"],
            "general_notes": ["general notes", "specification", "code", "standards", "workmanship", "tolerances", "contractor"]
        }

    def compile_wiki(self, sheets_text: Dict[str, str]) -> str:
        """
        Processes sheet text extracts, parses them into trade sections,
        writes individual markdown pages, and compiles the master drawings index drawings.md.
        """
        compiled_trades: Dict[str, List[str]] = {category: [] for category in self.categories}
        
        for sheet_num, text in sheets_text.items():
            for category, keywords in self.categories.items():
                # Check if text contains keywords
                if any(kw in text.lower() for kw in keywords):
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    relevant_lines = [
                        line for line in lines 
                        if any(kw in line.lower() for kw in keywords) or "note" in line.lower()
                    ]
                    if relevant_lines:
                        compiled_trades[category].append(
                            f"### Extracted from Sheet {sheet_num}\n" + "\n".join(relevant_lines)
                        )

        # Write markdown files
        for category, blocks in compiled_trades.items():
            page_content = f"# {category.replace('_', ' ').title()} Technical Specifications\n\n"
            if blocks:
                page_content += "\n\n---\n\n".join(blocks)
            else:
                page_content += "*No explicit spec lines extracted for this trade category.*"
                
            page_path = os.path.join(self.wiki_dir, f"{category}.md")
            with open(page_path, "w", encoding="utf-8") as f:
                f.write(page_content)

        # Compile and write drawings.md index file
        drawings_md_content = self._compile_drawings_index(sheets_text, list(self.categories.keys()))
        index_path = os.path.join(os.path.dirname(self.wiki_dir) or ".", "drawings.md")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(drawings_md_content)
            
        return index_path

    def _compile_drawings_index(self, sheets_text: Dict[str, str], categories: List[str]) -> str:
        """Generates the master register index (drawings.md) with links to wiki sub-pages."""
        register_rows = []
        for sheet_num, text in sheets_text.items():
            summary = "Text notes extract"
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 10]
            if lines:
                summary = lines[0][:80] + "..." if len(lines[0]) > 80 else lines[0]
            register_rows.append(f"| {sheet_num} | {summary} |")

        register_table = "\n".join(register_rows)
        
        # Generate clean relative paths for links
        wiki_links = "\n".join([
            f"* [{cat.replace('_', ' ').title()} Specifications]({os.path.basename(self.wiki_dir)}/{cat}.md)" 
            for cat in categories
        ])

        return f"""# Master Drawings Register & Project Wiki

This file serves as the main context block register for LLM-native processing.

## Drawings Register
| Sheet Number | Description / Primary Content |
| :--- | :--- |
{register_table}

## Technical Wiki Navigation
{wiki_links}

---
*Created by Drawings AI Wiki Compiler.*
"""

    def read_page(self, page_name: str) -> str:
        """Reads the content of a specific compiled wiki page or drawings.md index."""
        clean_name = page_name.replace(".md", "")
        page_path = os.path.join(self.wiki_dir, f"{clean_name}.md")
        
        if not os.path.exists(page_path):
            index_path = os.path.join(os.path.dirname(self.wiki_dir) or ".", f"{clean_name}.md")
            if os.path.exists(index_path):
                page_path = index_path
            else:
                raise FileNotFoundError(f"Wiki page not found: {page_name}")
                
        with open(page_path, "r", encoding="utf-8") as f:
            return f.read()

    def search_wiki(self, query: str) -> List[Dict[str, Any]]:
        """Searches across all compiled wiki markdown pages for a keyword query."""
        results = []
        query_lower = query.lower()
        
        if not os.path.exists(self.wiki_dir):
            return results
            
        for filename in os.listdir(self.wiki_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(self.wiki_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                matches = []
                for line_num, line in enumerate(content.split('\n'), 1):
                    if query_lower in line.lower():
                        matches.append({"line": line_num, "text": line.strip()})
                        
                if matches:
                    results.append({
                        "page": filename,
                        "matches_count": len(matches),
                        "snippet": matches[0]["text"],
                        "matches": matches[:5]  # limit snippet lines
                    })
        return results
