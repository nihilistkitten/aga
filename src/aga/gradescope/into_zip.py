"""The core entrypoint for the gradescope frontend.

More complete documentation is in `__init__.py`.
"""

from os.path import join as pathjoin
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from typing import Optional
from zipfile import ZipFile

from dill import dump  # type: ignore
from importlib_resources import files

from ..core import Output, Problem


class InvalidProblem(BaseException):
    """The Problem failed some golden tests."""


def into_gradescope_zip(problem: Problem[Output], path: Optional[str] = None) -> str:
    """Convert a Problem into a gradescope autograder zip, returning its location.

    This is the high-level entrypoint for this module.
    """
    _check_problem(problem)
    zip_name = _get_zipfile_dest(path, problem)

    with TemporaryDirectory() as tempdir:
        with ZipFile(zip_name, "w") as zip_f:
            path = _copy_resource_to(tempdir, "run_autograder")
            zip_f.write(path, arcname="run_autograder")

            path = _copy_resource_to(tempdir, "setup.sh")
            zip_f.write(path, arcname="setup.sh")

            path = _dump_problem_into_dir(problem, tempdir)
            zip_f.write(path, arcname="problem.pckl")

        return zip_name


def _get_zipfile_dest(path: Optional[str], problem: Problem[Output]) -> str:
    """Determine the destination in which to put the zip file.

    If `path` is none, this is the problem's name; otherwise it's just the provided
    path.
    """
    if path is None:
        return problem.name() + ".zip"
    else:
        return path


def _check_problem(problem: Problem[Output]) -> None:
    """Check whether `problem` is valid.

    Currently, this just runs the golden tests for problem.
    """
    try:
        problem.check()
    except AssertionError as err:
        raise InvalidProblem from err


def _copy_resource_to(
    tempdir: str, fname: str, package: str = "aga.gradescope.resources"
) -> str:
    """Copy the resource at package.fname to tempdir/fname, returning the dest path."""
    path = pathjoin(tempdir, fname)
    with files(package).joinpath(fname).open() as src:  # type: ignore
        with open(path, "w", encoding="UTF-8") as dest:
            copyfileobj(src, dest)

    return path


def _dump_problem_into_dir(
    problem: Problem[Output], tempdir: str, fname: str = "problem.pckl"
) -> str:
    """Dump a problem into a directory, returning the pckl file path."""
    path = pathjoin(tempdir, fname)
    _dump_problem_at_path(problem, path)
    return path


def _dump_problem_at_path(problem: Problem[Output], dest: str) -> None:
    """Pickle the problem into a destination."""
    with open(dest, "wb") as file:
        dump(problem, file)
