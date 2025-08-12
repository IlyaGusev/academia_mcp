import markdown
import re
import os
import subprocess
import shutil
import xml.dom.minidom
import xml.etree.ElementTree as etree
from typing import Optional, Any

from markdown.core import Markdown

from academia_mcp.files import get_workspace_dir


START_SINGLE_QUOTE_RE = re.compile(r"(^|\s|\")'")
START_DOUBLE_QUOTE_RE = re.compile(r"(^|\s|'|`)\"")
END_DOUBLE_QUOTE_RE = re.compile(r'"(,|\.|\s|$)')


MAIN_TEMPLATE = """\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{textcomp}}
\\usepackage{{amsmath}}
\\usepackage{{float}}
\\usepackage{{graphicx}}
\\usepackage{{enumitem}}
\\usepackage{{quoting}}
\\usepackage{{booktabs}}
\\usepackage{{caption}}
\\usepackage{{siunitx}}
\\sisetup{{
  group-separator = {{,}},
  output-decimal-marker = {{.}}
}}
\\usepackage{{hyperref}}

\\author{{Holosophos}}

\\begin{{document}}

{latex_content}

\\end{{document}}"""


IMAGE_TEMPLATE = """\\begin{{figure}}[H]
\\centering
\\includegraphics[width=\\linewidth]{{{src}}}
\\caption{{{alt}}}
\\end{{figure}}"""


TABLE_TEMPLATE = """
\\begin{{table}}[h]
\\begin{{tabular}}{{{descriptor}}}
{core}
\\hline
\\end{{tabular}}
\\\\[5pt]
\\caption{{{caption}}}
\\end{{table}}
"""

ITEMIZE_TEMPLATE = """
\\begin{{itemize}}
{content}
\\end{{itemize}}
"""

QUOTE_TEMPLATE = """
\\begin{{quotation}}
{content}
\\end{{quotation}}
"""

VERBATIM_TEMPLATE = """
\\begin{{verbatim}}
{content}
\\end{{verbatim}}
"""


MAKETITLE = """
% ----------------------------------------------------------------
\\maketitle
% ----------------------------------------------------------------
"""


def inline_html_latex(text: str) -> str:
    out = text
    if re.search(r"&ldquo;.*?&rdquo;", text, flags=re.DOTALL):
        out = out.replace("&ldquo;", "\\enquote{").replace("&rdquo;", "}")
    if re.search(r"&lsquo;.*?&rsquo;", text, flags=re.DOTALL):
        out = out.replace("&lsquo;", "\\enquote{").replace("&rsquo;", "}")
    if re.search(r"&ldquo;.*?&ldquo;", text, flags=re.DOTALL):
        out = out.replace("&ldquo;", "\\enquote{", 1).replace("&ldquo;", "}", 1)
    if re.search(r"&laquo;.*?&raquo;", text, flags=re.DOTALL):
        out = out.replace("&laquo;", "\\enquote{").replace("&raquo;", "}")
    out = out.replace("...", "\\dots")
    out = out.replace("&hellip;", "\\dots")
    out = out.replace("&ndash;", "--")
    out = out.replace("&mdash;", "---")
    out = out.replace("\\|", "|")
    return out


def unescape_html_entities(text: str) -> str:
    mapping = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def escape_latex_entities(text: str) -> str:
    out = unescape_html_entities(text)
    out = out.replace("%", "\\%")
    out = out.replace("&", "\\&")
    out = out.replace("#", "\\#")
    out = START_SINGLE_QUOTE_RE.sub(r"\g<1>`", out)
    out = START_DOUBLE_QUOTE_RE.sub(r"\g<1>``", out)
    out = END_DOUBLE_QUOTE_RE.sub(r"''\g<1>", out)
    return out


class LaTeXExtension(markdown.Extension):
    def __init__(self, configs: Optional[Any] = None) -> None:
        self.reset()

    def extendMarkdown(self, md: Markdown) -> None:
        self.md = md
        latex_tp = LaTeXTreeProcessor()
        math_pp = MathTextPostProcessor()
        table_pp = TableTextPostProcessor()
        image_pp = ImageTextPostProcessor()
        link_pp = LinkTextPostProcessor()
        unescape_html_pp = UnescapeHtmlTextPostProcessor()

        md.treeprocessors.register(latex_tp, "latex", 20)
        md.postprocessors.register(unescape_html_pp, "unescape_html", 20)
        md.postprocessors.register(math_pp, "math", 20)
        md.postprocessors.register(image_pp, "image", 20)
        md.postprocessors.register(table_pp, "table", 20)
        md.postprocessors.register(link_pp, "link", 20)

    def reset(self) -> None:
        pass


class LaTeXTreeProcessor(markdown.treeprocessors.Treeprocessor):
    def run(self, doc: etree.Element) -> None:
        latex_text = self.tolatex(doc)
        doc.clear()
        latex_node = etree.Element("plaintext")
        latex_node.text = latex_text
        doc.append(latex_node)

    def tolatex(self, ournode: etree.Element) -> str:
        buf = ""
        subcontent = ""

        if ournode.text:
            subcontent += escape_latex_entities(ournode.text)

        for child in list(ournode):
            subcontent += self.tolatex(child)

        tag = ournode.tag
        if tag == "h1":
            buf += "\n\\title{%s}\n" % subcontent
            buf += MAKETITLE
        elif tag == "h2":
            buf += "\n\n\\section{%s}\n" % subcontent
        elif tag == "h3":
            buf += "\n\n\\subsection{%s}\n" % subcontent
        elif tag == "h4":
            buf += "\n\\subsubsection{%s}\n" % subcontent
        elif tag == "hr":
            buf += "\\noindent\\makebox[\\linewidth]{\\rule{\\linewidth}{0.4pt}}"
        elif tag == "ul":
            buf += ITEMIZE_TEMPLATE.format(content=subcontent.strip())
        elif tag == "ol":
            buf += " \\begin{enumerate}"
            if "start" in ournode.attrib:
                start = int(ournode.attrib["start"]) - 1
                buf += "\\setcounter{enumi}{" + str(start) + "}"
            buf += f"\n{subcontent}\n\\end{{enumerate}}"
        elif tag == "li":
            buf += "\n  \\item %s" % subcontent.strip()
        elif tag == "blockquote":
            buf += QUOTE_TEMPLATE.format(content=subcontent.strip())
        elif tag == "pre":
            buf += VERBATIM_TEMPLATE.format(content=subcontent.strip())
        elif tag == "q":
            buf += "`%s'" % subcontent.strip()
        elif tag == "p":
            buf += "\n%s\n" % subcontent.strip()
        elif tag == "sup":
            buf += "\\footnote{%s}" % subcontent.strip()
        elif tag == "strong":
            buf += "\\textbf{%s}" % subcontent.strip()
        elif tag == "em":
            buf += "\\emph{%s}" % subcontent.strip()
        elif tag == "table":
            buf += "\n\n<table>%s</table>\n\n" % subcontent
        elif tag == "thead":
            buf += "<thead>%s</thead>" % subcontent
        elif tag == "tbody":
            buf += "<tbody>%s</tbody>" % subcontent
        elif tag == "tr":
            buf += "<tr>%s</tr>" % subcontent
        elif tag == "th":
            buf += "<th>%s</th>" % subcontent
        elif tag == "td":
            buf += "<td>%s</td>" % subcontent
        elif tag == "img":
            buf += '<img src="%s" alt="%s" />' % (
                ournode.get("src"),
                ournode.get("alt"),
            )
        elif tag == "a":
            href = ournode.get("href")
            assert href
            buf += '<a href="%s">%s</a>' % (
                escape_latex_entities(href),
                subcontent,
            )
        else:
            buf = subcontent

        if ournode.tail:
            buf += escape_latex_entities(ournode.tail)

        return buf


class Table2Latex:
    def convert_markdown_table(self, instr: str) -> str:
        lines = instr.split("\n")
        headers = lines[0].strip("|").split("|")
        cols = len(headers)
        buf = (
            "\\begin{table}[h]\n\\centering\n\\begin{tabular}{|"
            + "|".join(["l"] * cols)
            + "|}\n\\hline\n"
        )
        buf += (
            " & ".join([f"\\textbf{{{header.strip()}}}" for header in headers]) + " \\\\\n\\hline\n"
        )
        for line in lines[2:]:
            cells = line.strip("|").split("|")
            buf += " & ".join([cell.strip() for cell in cells]) + " \\\\\n\\hline\n"
        buf += "\\end{tabular}\n\\end{table}"
        return buf


class Img2Latex:
    def convert(self, instr: str) -> str:
        dom = xml.dom.minidom.parseString(instr)
        img = dom.documentElement
        assert img is not None
        src = img.getAttribute("src")
        alt = img.getAttribute("alt")
        return IMAGE_TEMPLATE.format(src=src, alt=alt)


class Link2Latex:
    def convert(self, instr: str) -> str:
        dom = xml.dom.minidom.parseString(instr)
        link = dom.documentElement
        assert link is not None
        href = link.getAttribute("href")
        matches = re.search(r">([^<]+)", instr)
        desc = ""
        if matches:
            desc = matches.group(1)
        return r"\href{%s}{%s}" % (href, desc) if href != desc else r"\url{%s}" % href


class ImageTextPostProcessor(markdown.postprocessors.Postprocessor):
    def run(self, instr: str) -> str:
        converter = Img2Latex()
        new_blocks = []
        for block in instr.split("\n\n"):
            stripped = block.strip()
            if stripped.startswith("<img"):
                stripped = re.sub(r"<\/?plaintext[^>]*>", "", stripped, flags=re.IGNORECASE)
                new_blocks.append(converter.convert(stripped).strip())
            else:
                new_blocks.append(block)
        return "\n\n".join(new_blocks)


class LinkTextPostProcessor(markdown.postprocessors.Postprocessor):
    def run(self, instr: str) -> str:
        converter = Link2Latex()
        new_blocks = []
        for block in instr.split("\n\n"):
            stripped = block.strip()
            matches = re.findall(r"<a[^>]*>[^<]+</a>", stripped)
            if matches:
                for match in matches:
                    stripped = stripped.replace(match, converter.convert(match).strip())
                new_blocks.append(stripped)
            else:
                new_blocks.append(block)
        return "\n\n".join(new_blocks)


class UnescapeHtmlTextPostProcessor(markdown.postprocessors.Postprocessor):
    def run(self, text: str) -> str:
        return unescape_html_entities(inline_html_latex(text))


class MathTextPostProcessor(markdown.postprocessors.Postprocessor):
    def run(self, instr: str) -> str:
        instr = re.sub(r"\$\$([^\$]*)\$\$", r"\\[\1\\]", instr)
        instr = re.sub(r"\$([^\$]*)\$", r"\\(\1\\)", instr)
        instr = instr.replace("\\lt", "<").replace(" * ", " \\cdot ").replace("\\del", "\\partial")
        return instr


class TableTextPostProcessor(markdown.postprocessors.Postprocessor):
    def run(self, instr: str) -> str:
        converter = Table2Latex()
        new_blocks = []
        for block in instr.split("\n\n"):
            stripped = block.strip()
            if re.match(r"\|.*\|", stripped):  # Check for Markdown table
                new_blocks.append(converter.convert_markdown_table(stripped).strip())
            else:
                new_blocks.append(block)
        return "\n\n".join(new_blocks)


def convert_md_to_latex(md_content: str) -> str:
    md = markdown.Markdown(extensions=[LaTeXExtension()])
    latex_content = md.convert(md_content)
    latex_content = re.sub(r"<\/?plaintext[^>]*>", "", latex_content, flags=re.IGNORECASE)
    return MAIN_TEMPLATE.format(latex_content=latex_content)


def md_to_pdf(markdown_text: str, output_filename: str = "output") -> str:
    """
    Convert Markdown to PDF via LaTeX.

    Args:
        markdown_text: Markdown text
        output_filename: Output filename (without extension)

    Returns:
        Message about the compilation result
    """

    latex_code = convert_md_to_latex(markdown_text)

    temp_dir = get_workspace_dir() / "temp_latex"
    temp_dir.mkdir(parents=True, exist_ok=True)

    tex_file_path = temp_dir / "temp.tex"
    with open(tex_file_path, "w", encoding="utf-8") as f:
        f.write(latex_code)

    try:
        subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory",
                temp_dir,
                tex_file_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

    except subprocess.TimeoutExpired:
        return "Compilation timed out after 30 seconds"
    except subprocess.CalledProcessError as e:
        error_msg = e.stdout.decode("utf-8")
        error_lines = [
            line for line in error_msg.split("\n") if "error" in line.lower() or "!" in line
        ]
        if error_lines:
            return "Compilation failed. LaTeX errors:\n" + "\n".join(error_lines)
        return f"Compilation failed. Full LaTeX output:\n{error_msg}"

    pdf_path = os.path.join(temp_dir, "temp.pdf")
    output_pdf_path = os.path.join(get_workspace_dir(), f"{output_filename}.pdf")

    if os.path.exists(pdf_path):
        shutil.move(pdf_path, output_pdf_path)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return f"Compilation successful! PDF file saved as {output_filename}.pdf"

    return "Compilation completed, but PDF file was not created. Check LaTeX code for errors."
