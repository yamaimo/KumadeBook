import kumade as ku

import shutil
import subprocess
import sys
from pathlib import Path

project_dir = Path(__file__).parent

# preprocess.pyをロードできるようにする
sys.path.append(str(project_dir))
from preprocess import preprocess

ku.set_default("build")

# ebook: 電子用, print: 印刷用
variants = ["ebook", "print"]


# Files ----------

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

json_files = ["package.json", "package-lock.json"]

css_files = ["countup.css", "reset_page.css"]

theme_dir = project_dir / "theme"

build_dir = {}
pdf_path = {}
theme_css_path = {}
assets_dir = {}
assets_paths: dict[str, list[Path]] = {}
pp_md_paths: dict[str, list[Path]] = {}
for variant in variants:
    build_dir[variant] = project_dir / f"build_{variant}"
    pdf_path[variant] = build_dir[variant] / f"KumadeBook.{variant}.pdf"
    theme_css_path[variant] = theme_dir / f"theme_{variant}.css"
    assets_dir[variant] = project_dir / f"assets_{variant}"
    assets_paths[variant] = []  # あとで追加していく
    pp_md_paths[variant] = []  # あとで追加していく


# Initialize build directory ----------

for variant in variants:
    ku.directory(build_dir[variant])

    depend_paths = []
    for json_file in json_files:
        src_json = project_dir / json_file
        dst_json = build_dir[variant] / json_file
        depend_paths.append(dst_json)

        @ku.file(dst_json)
        @ku.depend(build_dir[variant], src_json)
        @ku.bind_args(src_json, dst_json)
        def copy_json(src: Path, dst: Path) -> None:
            shutil.copy(src, dst)

    node_modules_dir = build_dir[variant] / "node_modules"

    @ku.file(node_modules_dir)
    @ku.depend(*depend_paths)
    @ku.bind_args(build_dir[variant])
    def install_dependencies(work_dir: Path) -> None:
        subprocess.run(["npm", "install"], cwd=work_dir)

    @ku.task(f"init_build_{variant}")
    @ku.help(f"Initialize build directory for {variant}.")
    @ku.depend(node_modules_dir)
    def init_build_dir() -> None:
        pass


# Copy assets ----------

for variant in variants:
    src_config = assets_dir[variant] / "vivliostyle.config.js"
    dst_config = build_dir[variant] / "vivliostyle.config.js"
    assets_paths[variant].append(dst_config)

    @ku.file(dst_config)
    @ku.depend(build_dir[variant], src_config)
    @ku.bind_args(src_config, dst_config)
    def copy_config(src: Path, dst: Path) -> None:
        shutil.copy(src, dst)

    build_image_dir = build_dir[variant] / "images"
    ku.directory(build_image_dir)

    for src_image in (assets_dir[variant] / "images").iterdir():
        dst_image = build_image_dir / src_image.name
        assets_paths[variant].append(dst_image)

        @ku.file(dst_image)
        @ku.depend(build_image_dir, src_image)
        @ku.bind_args(src_image, dst_image)
        def copy_image(src: Path, dst: Path) -> None:
            shutil.copy(src, dst)

    for css_file in css_files:
        src_css = project_dir / css_file
        dst_css = build_dir[variant] / css_file
        assets_paths[variant].append(dst_css)

        @ku.file(dst_css)
        @ku.depend(build_dir[variant], src_css)
        @ku.bind_args(src_css, dst_css)
        def copy_css(src: Path, dst: Path) -> None:
            shutil.copy(src, dst)

    build_theme_dir = build_dir[variant] / "theme"
    ku.directory(build_theme_dir)

    dst_theme_css = build_theme_dir / theme_css_path[variant].name
    assets_paths[variant].append(dst_theme_css)

    @ku.file(dst_theme_css)
    @ku.depend(build_theme_dir, theme_css_path[variant])
    @ku.bind_args(theme_css_path[variant], dst_theme_css)
    def copy_theme_css(src: Path, dst: Path) -> None:
        shutil.copy(src, dst)

    @ku.task(f"copy_assets_{variant}")
    @ku.help(f"Copy assets for {variant}.")
    @ku.depend(*assets_paths[variant])
    def copy_assets() -> None:
        pass


# Preprocess sources ----------

for variant in variants:
    for md_file in md_files:
        md_path = project_dir / md_file
        pp_md_path = build_dir[variant] / md_file
        pp_md_paths[variant].append(pp_md_path)

        @ku.file(pp_md_path)
        @ku.depend(build_dir[variant], md_path)
        @ku.bind_args(md_path, pp_md_path)
        def preprocess_md(src: Path, dst: Path) -> None:
            preprocess(src, dst)

    @ku.task(f"pp_md_{variant}")
    @ku.help(f"Preprocess sources for {variant}.")
    @ku.depend(*pp_md_paths[variant])
    def preprocess_sources() -> None:
        pass


# Build PDF ----------

for variant in variants:
    @ku.task(f"build_{variant}")
    @ku.help(f"Build PDF for {variant}.")
    @ku.depend(pdf_path[variant])
    def build() -> None:
        pass

    depend_paths = [*assets_paths[variant], *pp_md_paths[variant]]

    @ku.file(pdf_path[variant])
    @ku.depend(f"init_build_{variant}", *depend_paths)
    @ku.bind_args(build_dir[variant])
    def build_pdf(work_dir: Path) -> None:
        subprocess.run(["npm", "run", "build"], cwd=work_dir)

build_tasks = [f"build_{variant}" for variant in variants]

@ku.task("build")
@ku.help(f"Build all PDFs.")
@ku.depend(*build_tasks)
def build_all() -> None:
    pass

 
# Build Theme ----------

theme_node_modules_dir = theme_dir / "node_modules"
scss_dir = theme_dir / "scss"
scss_paths = list(scss_dir.glob("*.scss"))
theme_built_path = theme_dir / "theme_built"

@ku.file(theme_node_modules_dir)
def install_theme_dependencies() -> None:
    subprocess.run(["npm", "install"], cwd=theme_dir)

for variant in variants:
    @ku.file(theme_css_path[variant])
    @ku.depend(theme_built_path)
    def create_css() -> None:
        pass

@ku.file(theme_built_path)
@ku.depend(theme_node_modules_dir, *scss_paths)
def build_theme() -> None:
    subprocess.run(["npm", "run", "build"], cwd=theme_dir)
    theme_built_path.touch()


# Open PDF (for mac) ----------

for variant in variants:
    @ku.task(f"open_{variant}")
    @ku.help(f"Open PDF for {variant}.")
    @ku.depend(f"build_{variant}")
    @ku.bind_args(pdf_path[variant])
    def open_pdf(path: Path) -> None:
        subprocess.run(["open", str(path)])
 
 
# Delete outputs ----------

output_paths = list(build_dir.values())

ku.clean("clean", output_paths, help="Delete outputs.")
