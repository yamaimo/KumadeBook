import kumade as ku

from pathlib import Path
import subprocess

ku.set_default("greet")

help_file = Path("help.txt")

@ku.task("greet")
@ku.depend(help_file)
def greeting() -> None:
    print("Hi, this is Kumade.")
    print(f"See {help_file}.")

@ku.file(help_file)
def create_help_file() -> None:
    with help_file.open("w") as outfile:
        subprocess.run(["kumade", "-h"], stdout=outfile)
