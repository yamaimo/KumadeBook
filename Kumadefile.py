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
@ku.depend("init_project", *md_paths)
def build_pdf() -> None:
    subprocess.run(["npm", "run", "build"])


# Delete outputs ----------

output_paths = [pdf_path, *html_paths, pub_json_path]

ku.clean("clean", output_paths, help="Delete outputs.")
