import re
import subprocess
import shutil
import tempfile
import json
from pathlib import Path


from academia_mcp.files import get_workspace_dir, DEFAULT_LATEX_TEMPLATES_DIR_PATH
from academia_mcp.pdf import parse_pdf_file


def get_latex_templates_list() -> str:
    """
    Get the list of available latex templates.
    Always use one of the templates from the list.

    Returns a JSON list serialized to a string.
    Use `json.loads` to deserialize the result.
    """
    return json.dumps([str(path.name) for path in DEFAULT_LATEX_TEMPLATES_DIR_PATH.glob("*")])


def get_latex_template(template_name: str) -> str:
    """
    Get the latex template by name.

    Returns a JSON object serialized to a string.
    Use `json.loads` to deserialize the result.
    The structure is: {"template": "...", "style": "..."}

    Args:
        template_name: The name of the latex template.
    """
    template_dir_path = DEFAULT_LATEX_TEMPLATES_DIR_PATH / template_name
    if not template_dir_path.exists():
        raise FileNotFoundError(
            f"Template {template_name} not found in {DEFAULT_LATEX_TEMPLATES_DIR_PATH}"
        )
    template_path = template_dir_path / f"{template_name}.tex"
    style_path = template_dir_path / f"{template_name}.sty"
    if not template_path.exists():
        raise FileNotFoundError(f"Template file {template_path} not found in {template_dir_path}")
    if not style_path.exists():
        raise FileNotFoundError(f"Style file {style_path} not found in {template_dir_path}")
    return json.dumps({"template": template_path.read_text(), "style": style_path.read_text()})


def compile_latex(
    input_filename: str, output_filename: str = "output.pdf", timeout: int = 60
) -> str:
    """
    Compile a latex file.

    Returns a string with the result of the compilation.

    Args:
        input_filename: The path to the latex file.
        output_filename: The path to the output pdf file.
        timeout: The timeout for the compilation. 60 seconds by default.
    """
    input_filename_path = Path(input_filename)
    if not input_filename_path.exists():
        input_filename_path = Path(get_workspace_dir()) / input_filename
    assert input_filename_path.exists(), f"Input file {input_filename} does not exist"
    latex_code = input_filename_path.read_text(encoding="utf-8")

    if shutil.which("pdflatex") is None:
        return "pdflatex is not installed or not found in PATH."

    destination_name = (
        output_filename if output_filename.lower().endswith(".pdf") else f"{output_filename}.pdf"
    )

    try:
        with tempfile.TemporaryDirectory(
            dir=str(get_workspace_dir()), prefix="temp_latex_"
        ) as temp_dir:
            temp_dir_path = Path(temp_dir)
            tex_filename = "temp.tex"
            pdf_filename = "temp.pdf"
            tex_file_path = temp_dir_path / tex_filename
            tex_file_path.write_text(latex_code, encoding="utf-8")

            # Detect and copy local .sty packages referenced by \usepackage{...}
            # Supports optional arguments: \usepackage[opts]{pkgA,pkgB}
            try:
                package_names: set[str] = set()
                for match in re.finditer(r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}", latex_code):
                    for name in match.group(1).split(","):
                        pkg = name.strip()
                        if pkg:
                            package_names.add(pkg)

                for pkg in package_names:
                    sty_name = f"{pkg}.sty"
                    for candidate in DEFAULT_LATEX_TEMPLATES_DIR_PATH.rglob(sty_name):
                        shutil.copyfile(candidate, temp_dir_path / sty_name)
                        break
            except Exception:
                pass

            try:
                bib_source_path = input_filename_path.parent / "references.bib"
                if bib_source_path.exists():
                    shutil.copyfile(bib_source_path, temp_dir_path / "references.bib")
            except Exception:
                pass

            try:
                subprocess.run(
                    [
                        "latexmk",
                        "-pdf",
                        "-interaction=nonstopmode",
                        "-file-line-error",
                        "-diagnostics",
                        tex_filename,
                    ],
                    cwd=str(temp_dir_path),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                return f"Compilation timed out after {timeout} seconds"
            except subprocess.CalledProcessError as e:
                combined_output = (e.stdout or "") + "\n" + (e.stderr or "")
                log_path = temp_dir_path / "temp.log"
                if log_path.exists():
                    log_content = log_path.read_text(encoding="utf-8", errors="ignore")
                    combined_output = combined_output + "\n\ntemp.log content:\n" + log_content
                return f"Compilation failed. Full LaTeX output:\n{combined_output}"

            pdf_path = temp_dir_path / pdf_filename
            output_pdf_path = Path(get_workspace_dir()) / destination_name

            if pdf_path.exists():
                shutil.move(str(pdf_path), str(output_pdf_path))
                return f"Compilation successful! PDF file saved as {destination_name}"

            return (
                "Compilation completed, but PDF file was not created. Check LaTeX code for errors."
            )
    except Exception as e:
        return f"Compilation failed due to an unexpected error: {e}"


def read_pdf(pdf_path: str) -> str:
    """
    Read a PDF file to text from the file system.

    Args:
        pdf_path: The path to the pdf file in the working directory.

    Returns a JSON-serialized list of strings where each string is a page of the pdf file.
    """
    full_path = Path(get_workspace_dir()) / pdf_path
    return json.dumps(parse_pdf_file(full_path))
