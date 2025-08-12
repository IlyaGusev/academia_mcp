from academia_mcp.tools.md_to_pdf import convert_md_to_latex, md_to_pdf


TEST_MD_BASIC = """
# Markdown syntax guide

## Headers

### This is a Heading h3
###### This is a Heading h6

## Emphasis

*This text will be italic*
_This will also be italic_

**This text will be bold**
__This will also be bold__

_You **can** combine them_
"""

TEST_MD_TABLES = """
## Tables

| Left columns  | Right columns |
| ------------- |:-------------:|
| left foo      | right foo     |
| left bar      | right bar     |
| left baz      | right baz     |
"""

TEST_MD_LINKS = """
## Links

You may be using [Markdown Live Preview](https://markdownlivepreview.com/).
"""

TEST_MD_IMAGES = """
## Images

![This is an alt text.](/image/sample.webp "This is a sample image.")
"""

TEST_MD_LISTS = """
## Lists

### Unordered

* Item 1
* Item 2
* Item 2a
* Item 2b
    * Item 3a
    * Item 3b

### Ordered

1. Item 1
2. Item 2
3. Item 3
    1. Item 3a
    2. Item 3b
"""


def test_md_to_latex_basic() -> None:
    latex = convert_md_to_latex(TEST_MD_BASIC)
    assert "\\documentclass{article}" in latex
    assert "\\title{Markdown syntax guide}" in latex
    assert "\\section{Headers}" in latex
    assert "\\section{Emphasis}" in latex
    assert "\\subsection{This is a Heading h3}" in latex
    assert "\\emph{This text will be italic}" in latex
    assert "\\emph{This will also be italic}" in latex
    assert "\\textbf{This text will be bold}" in latex
    assert "\\textbf{This will also be bold}" in latex
    assert "\\emph{You \\textbf{can} combine them}" in latex


def test_md_to_latex_tables() -> None:
    latex = convert_md_to_latex(TEST_MD_TABLES)
    assert "\\begin{table}[h]" in latex
    assert "\\begin{tabular}{|l|l|}" in latex
    assert "left foo & right foo" in latex


def test_md_to_latex_links() -> None:
    latex = convert_md_to_latex(TEST_MD_LINKS)
    assert (
        "You may be using \\href{https://markdownlivepreview.com/}{Markdown Live Preview}." in latex
    )


def test_md_to_latex_images() -> None:
    latex = convert_md_to_latex(TEST_MD_IMAGES)
    assert "\\begin{figure}" in latex
    assert "\\includegraphics[width=\\linewidth]{/image/sample.webp}" in latex
    assert "\\caption{This is an alt text.}" in latex
    assert "\\end{figure}" in latex


def test_md_to_latex_lists() -> None:
    latex = convert_md_to_latex(TEST_MD_LISTS)
    assert "\\begin{itemize}" in latex
    assert "\\end{itemize}" in latex
    assert "\\begin{enumerate}" in latex
    assert "\\end{enumerate}" in latex
    assert "\\item Item 3a" in latex


def test_md_to_pdf() -> None:
    result = md_to_pdf(TEST_MD_LISTS, "output")
    assert "Compilation successful" in result
