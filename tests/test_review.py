import json
import tempfile
from pathlib import Path

from academia_mcp.tools.review import review_pdf
from academia_mcp.tools.latex import compile_latex_from_file, get_latex_template


async def test_review_pdf() -> None:
    template = json.loads(get_latex_template("agents4science_2025"))
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        tex_filename = "temp.tex"
        tex_file_path = temp_dir_path / tex_filename
        pdf_filename = "test.pdf"
        tex_file_path.write_text(template["template"], encoding="utf-8")
        result = compile_latex_from_file(str(tex_file_path), pdf_filename)
        assert "Compilation successful" in result
        review = await review_pdf(str(pdf_filename))
        assert review
