# Requires Python 3.10

import argparse
import itertools
import os
import re
import shutil
import subprocess
import sys
import stat
import traceback

from typing import Any, Callable
from pathlib import Path
from pycparser import c_ast, parse_file
from os import PathLike

# -----
# Utility functions
# -----

def print_stage_name(*text: Any):
    print("•", *text)


def echo_call(bin: PathLike | str, *args: str):
    print(">", str(bin), *args)


def run(
    bin_name: str,
    *args: str,
    cwd: str | Path | None = None,
    echo: bool = True,
    silent: bool = False
):
    if echo:
        echo_call(bin_name, *args)

    if silent:
        subprocess.check_output([bin_name] + list(args), cwd=cwd)
    else:
        subprocess.check_call([bin_name] + list(args), cwd=cwd)


def git(command: str, *args: str, cwd: str | Path | None = None, echo: bool = True):
    run("git", command, *args, cwd=cwd, echo=echo)


def git_output(*args: str, cwd: str | None = None, echo: bool = True) -> str:
    if echo:
        echo_call("git", *args)

    return subprocess.check_output(["git"] + list(args), cwd=cwd).decode("UTF8")


def path(root: PathLike | str, *args: PathLike | str) -> Path:
    return Path(root).joinpath(*args)

def local_path(*args: PathLike | str) -> Path:
    return path(Path(__file__).parent, *args)

# From: https://github.com/gitpython-developers/GitPython/blob/ea43defd777a9c0751fc44a9c6a622fc2dbd18a0/git/util.py#L101
# Windows has issues deleting readonly files that git creates
def git_rmtree(path: os.PathLike) -> None:
    """Remove the given recursively.
    :note: we use shutil rmtree but adjust its behaviour to see whether files that
        couldn't be deleted are read-only. Windows will not remove them in that case"""

    def onerror(func: Callable, path: os.PathLike, _) -> None:
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)

        try:
            func(path)  # Will scream if still not possible to delete.
        except Exception:
            raise

    return shutil.rmtree(path, False, onerror)


# -----
# Compiler invocations functions
# -----

def run_cl(input_path: Path, cwd: PathLike | str | None = None) -> bytes:
    args: list[str | os.PathLike] = [
        "cl",
        "/E",
        "/Za",
        "/Zc:wchar_t",
        input_path,
    ]

    result = subprocess.check_output(args, cwd=cwd)
    # Windows-specific fix to replace some page feeds that may be present in the
    # original system headers
    result = result.replace(b"\x0c", b"")
        
    return result


def run_clang(input_path: Path, cwd: PathLike | str | None = None) -> bytes:
    args: list[str | os.PathLike] = [
        "clang",
        "-E",
        "-fuse-line-directives",
        "-std=c99",
        "-pedantic-errors",
        input_path,
    ]

    return subprocess.check_output(args, cwd=cwd)


def run_c_preprocessor(input_path: Path, cwd: PathLike | str | None = None) -> bytes:
    if sys.platform == "win32":
        return run_cl(input_path)

    return run_clang(input_path, cwd=cwd)

# -----
# C symbols lookup / formatting
# -----

class DefNamesVisitor(c_ast.NodeVisitor):
    decls = []

    def add_name(self, name):
        assert(name != None)
        self.decls.append(name)

    def visit_Decl(self, node):
        if node.name != None:
            self.add_name(node.name)
        c_ast.NodeVisitor.generic_visit(self, node)

    def visit_FuncDef(self, node):
        self.add_name(node.decl.name)

    def visit_Typedef(self, node):
        self.add_name(node.name)
        c_ast.NodeVisitor.generic_visit(self, node)

    def visit_Enumerator(self, node):
        self.add_name(node.name)

    def visit_Struct(self, node):
        if node.name != None:
            self.add_name(node.name)
        c_ast.NodeVisitor.generic_visit(self, node)

def flatten(array):
    return list(itertools.chain.from_iterable(array))

def expand(line):
    # Do camelCase/PascalCase expansion
    matches = re.findall(r'.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', line)
    # Split snake_case strings
    matches = flatten([term.split("_") for term in matches])
    # Split around numbers
    matches = flatten([re.split(r'[0-9]+', term) for term in matches])

    return [term for term in matches if len(term) > 3 and not term.isnumeric()]

def process(lines):
    result = set([])
    for line in lines:
        for term in expand(line):
            result.add(term)

    return sorted(result)


# -----
# Main logic
# -----

Z3_REPO = "https://github.com/Z3Prover/z3.git"
TEMP_FOLDER_NAME = "temp"

def create_temporary_folder() -> Path:
    temp_path = local_path(TEMP_FOLDER_NAME)
    if temp_path.exists():
        git_rmtree(temp_path)

    os.mkdir(temp_path)

    return temp_path


def clone_repo(tag_or_branch: str | None, repo: str, clone_path: str):
    if tag_or_branch is None:
        git("clone", repo, "--depth=1", clone_path)
    else:
        git("clone", repo, clone_path)
        git("checkout", tag_or_branch, cwd=clone_path)


def clone_z3(tag_or_branch: str | None) -> Path:
    # Create temp path
    temp_path = create_temporary_folder()

    print_stage_name("Cloning Z3...")

    z3_clone_path = str(path(temp_path, "z3").absolute())

    clone_repo(tag_or_branch, Z3_REPO, z3_clone_path)

    return Path(z3_clone_path)


# -----
# Entry point
# -----


def main() -> int:
    def make_argparser() -> argparse.ArgumentParser:
        argparser = argparse.ArgumentParser()
        argparser.add_argument(
            "-b",
            "--z3_tag",
            type=str,
            help="A tag or branch to clone from the Z3 repository. If not provided, defaults to latest commit of default branch.",
        )
        argparser.add_argument(
            '--file',
            dest='file_name',
            type=Path,
            default="input.h",
            help="File to use to generate a preprocessed file to parse with pycparser. Defaults to 'input.h'"
        )
        argparser.add_argument(
            '--keep-repo',
            dest='keep_repo',
            action="store_true",
            help="Whether to skip removing the cloned Z3 repository after the script is done."
        )

        return argparser

    argparser = make_argparser()
    args = argparser.parse_args()
    target_file = 'z3-solver.txt'

    z3_path = clone_z3(args.z3_tag)

    print_stage_name("Running preprocessor...")
    file_name = local_path(args.file_name)

    output_file = run_c_preprocessor(file_name, cwd=local_path())

    output_path = file_name.with_suffix(".h.output")
    with open(output_path, "wb") as f:
        f.truncate(0)
        f.write(output_file)

    try:
        print_stage_name(f"Parsing {output_path.name}...")

        ast = parse_file(output_path.resolve(), use_cpp=False)

        print_stage_name("Parsing succeeded! Collecting parsed declarations...")

        visitor = DefNamesVisitor()
        visitor.visit(ast)

        lines = visitor.decls

        print_stage_name(f"Collecting succeeded! Processing results...")

        lines = process(lines)

        print_stage_name(f"Processing succeeded! Writing results to {target_file}...")

        with open(target_file, 'w') as f:
            f.truncate(0)
            f.write("\n".join(lines))

        print_stage_name("Success!")
    except:
        print(traceback.format_exc())
        return 1
    
    if not args.keep_repo:
        git_rmtree(z3_path)
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as err:
        sys.exit(err.returncode)
    except KeyboardInterrupt:
        sys.exit(1)
