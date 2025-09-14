import json
import tempfile
from pathlib import Path

from academia_mcp.tools.latex import (
    compile_latex,
    get_latex_template,
    get_latex_templates_list,
    read_pdf,
)


def test_latex_get_latex_templates_list() -> None:
    templates_list = json.loads(get_latex_templates_list())
    assert len(templates_list) > 0
    assert "agents4science_2025" in templates_list


def test_latex_get_latex_template() -> None:
    result = json.loads(get_latex_template("agents4science_2025"))
    assert "template" in result
    assert "style" in result
    assert result["template"] is not None
    assert result["style"] is not None


def test_latex_compile_latex_from_file() -> None:
    template = json.loads(get_latex_template("agents4science_2025"))
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        tex_filename = "temp.tex"
        tex_file_path = temp_dir_path / tex_filename
        pdf_filename = "test.pdf"
        tex_file_path.write_text(template["template"], encoding="utf-8")
        result = compile_latex(str(tex_file_path), pdf_filename)
    assert "Compilation successful" in result


def test_latex_read_pdf() -> None:
    template = json.loads(get_latex_template("agents4science_2025"))
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        tex_filename = "temp.tex"
        tex_file_path = temp_dir_path / tex_filename
        pdf_filename = "test.pdf"
        tex_file_path.write_text(template["template"], encoding="utf-8")
        compile_latex(str(tex_file_path), pdf_filename)
        read_result = json.loads(read_pdf(pdf_filename))
        assert read_result
        assert "Page 1" in read_result[0]
