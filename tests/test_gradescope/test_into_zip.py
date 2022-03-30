"""Tests for the gradescope frontend."""

# this is raised whenever you access any member of the unpickled objects
# pylint: disable=no-member

import os
from io import TextIOWrapper
from typing import Iterable, Tuple, TypeVar
from zipfile import ZipFile

import pytest
from dill import load  # type: ignore
from importlib_resources import files

from aga.core import Problem
from aga.gradescope import InvalidProblem, into_gradescope_zip

Output = TypeVar("Output")

# location of resources file, for testing imports
RESOURCES_DIR = "aga.gradescope.resources"


@pytest.fixture(name="gradescope_zip")
def fixture_gradescope_zip(
    valid_problem: Problem[Output],
) -> Iterable[Tuple[Problem[Output], str]]:
    """Construct a zip from a problem, returning the problem and the zip path."""

    zip_path = into_gradescope_zip(valid_problem)

    # when you yield from a pytest fixture, it runs the test immediately, and then
    # returns to the fixture for cleanup
    yield (valid_problem, zip_path)

    os.remove(zip_path)


def test_into_gradescope_zip_path(gradescope_zip: Tuple[Problem[Output], str]) -> None:
    """Test that into_gradescope_zip puts the zip file at the right plase."""

    orig_problem, zip_path = gradescope_zip

    assert zip_path == f"{orig_problem.name()}.zip"


def test_into_gradescope_zip_problem(
    gradescope_zip: Tuple[Problem[Output], str]
) -> None:
    """Test that into_gradescope_zip pickles the provided problem correctly."""

    orig_problem, zip_path = gradescope_zip

    with ZipFile(zip_path) as zip_f:
        with zip_f.open("problem.pckl") as problem:
            problem_loaded = load(problem)  # type: Problem[Output]
            problem_loaded.check()
            assert problem_loaded.name() == orig_problem.name()


@pytest.mark.parametrize("file", ("run_autograder", "setup.sh"))
def test_into_gradescope_zip_run_autograder(
    gradescope_zip: Tuple[Problem[Output], str], file: str
) -> None:
    """Test that into_gradescope_zip copies files correctly."""

    _, zip_path = gradescope_zip

    with ZipFile(zip_path) as zip_f:
        with zip_f.open(file, "r") as zip_byte_stream:
            with TextIOWrapper(zip_byte_stream) as zipped_file:
                with files(RESOURCES_DIR).joinpath(file).open() as src:  # type: ignore
                    assert zipped_file.read() == src.read()


def test_into_gradescope_zip_custom_path(valid_problem: Problem[Output]) -> None:
    """Test into_gradescope_zip with a custom path."""

    try:
        zip_path = into_gradescope_zip(valid_problem, "archive.zip")
        assert zip_path == "archive.zip"
    finally:
        os.remove(zip_path)


def test_into_gradescope_zip_incorrect_problem(diff_bad_impl: Problem[int]) -> None:
    """Test into_gradescope_zip with an invalid problem."""

    with pytest.raises(InvalidProblem):
        zip_path = into_gradescope_zip(diff_bad_impl)

        # should never be run if the test works, but if not, we want to clean up
        os.remove(zip_path)
