import kumade as ku

import subprocess
from pathlib import Path

ku.set_default("build")

project_dir = Path(__file__).parent


# Files ----------

pdf_path = project_dir / "KumadeBook.pdf"

md_files = [
    "cover1.md",
    "opening.md",
    "toc.md",
    "chap1_intro.md",
    "chap2_getstart.md",
    "chap3_kumadefile.md",
    "chap4_usecase.md",
    "closing.md",
    "cover4.md",
]

theme_dir = project_dir / "theme"

css_path = theme_dir / "theme_ebook.css"


# Initialize project ----------

node_modules_dir = project_dir / "node_modules"

@ku.task("init_project")
@ku.help("Initialize project.")
@ku.depend(node_modules_dir)
def init_project() -> None:
    pass

@ku.file(node_modules_dir)
def install_dependencies() -> None:
    subprocess.run(["npm", "install"])


# Build PDF ----------

md_paths = [project_dir / md_file for md_file in md_files]
html_paths = [md_path.with_suffix(".html") for md_path in md_paths]
pub_json_path = project_dir / "publication.json"

@ku.task("build")
@ku.help("Build PDF.")
@ku.depend(pdf_path)
def build() -> None:
    pass

@ku.file(pdf_path)
@ku.depend("init_project", css_path, *md_paths)
def build_pdf() -> None:
    subprocess.run(["npm", "run", "build"])


# Build Theme ----------

theme_node_modules_dir = theme_dir / "node_modules"
scss_dir = theme_dir / "scss"
scss_paths = list(scss_dir.glob("*.scss"))

@ku.file(theme_node_modules_dir)
def install_theme_dependencies() -> None:
    subprocess.run(["npm", "install"], cwd=theme_dir)

@ku.file(css_path)
@ku.depend(theme_node_modules_dir, *scss_paths)
def build_theme() -> None:
    subprocess.run(["npm", "run", "build"], cwd=theme_dir)


# Open PDF (for mac) ----------

@ku.task("open")
@ku.help("Open PDF.")
@ku.depend("build")
def open_pdf() -> None:
    subprocess.run(["open", str(pdf_path)])


# Delete outputs ----------

output_paths = [pdf_path, *html_paths, pub_json_path]

ku.clean("clean", output_paths, help="Delete outputs.")
