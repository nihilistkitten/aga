"""Tests for the gradescope frontend."""

# this is raised whenever you access any member of the unpickled objects
# pylint: disable=no-member

import json
import os
from importlib.resources import files
from inspect import getmembers, getsource, ismodule
from io import TextIOWrapper
from os.path import dirname
from os.path import join as pathjoin
from pathlib import Path
from typing import Any, Iterable, Tuple, TypeVar
from zipfile import ZipFile

import pytest
from dill import load  # type: ignore
from pytest_mock import MockerFixture

import aga  # for source inspection
from aga.core import Problem
from aga.gradescope import InvalidProblem, into_gradescope_zip
from aga.gradescope.main import gradescope_main

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


def test_into_gradescope_zip_source(
    gradescope_zip: Tuple[Problem[Output], str]
) -> None:
    """Test that into_gradescope_zip archives the library source correctly."""

    _, zip_path = gradescope_zip
    with ZipFile(zip_path) as zip_f:
        for (name, module) in getmembers(aga, ismodule):
            # don't check gradescope because it's a subdirectory and I'm too lazy to
            # write special handling or recursion right now
            if name != "gradescope":
                with zip_f.open(pathjoin("aga", name + ".py")) as src:
                    unzipped_core_source = src.read()
                    core_source = bytes(getsource(module), "UTF-8")
                    assert unzipped_core_source == core_source


def test_into_gradescope_zip_problem(
    gradescope_zip: Tuple[Problem[Output], str]
) -> None:
    """Test that into_gradescope_zip pickles the provided problem correctly."""

    orig_problem, zip_path = gradescope_zip

    with ZipFile(zip_path) as zip_f:
        with zip_f.open("problem.pckl") as problem:
            problem_loaded = load(problem)  # type: Problem[Output]
            problem_loaded.run_golden_tests()
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
        os.remove("archive.zip")


def test_into_gradescope_zip_incorrect_problem(diff_bad_impl: Problem[int]) -> None:
    """Test into_gradescope_zip with an invalid problem."""

    with pytest.raises(InvalidProblem):
        zip_path = into_gradescope_zip(diff_bad_impl)

        # should never be run if the test works, but if not, we want to clean up
        os.remove(zip_path)


def get_gs_json(
    problem: Problem[Any], source: str, mocker: MockerFixture, tmp_path: Path
) -> Any:
    """Get the gradescope JSON output for the given problem and submission source."""
    mocked_load_problem = mocker.patch("aga.gradescope.main.load_problem")
    mocked_load_problem.return_value = problem

    output = pathjoin(tmp_path, "results.json")
    gradescope_main(submission_dir=dirname(source), output_file=output)

    with open(output, encoding="UTF-8") as file:
        return json.load(file)


@pytest.fixture(name="gs_json_square")
def fixture_gs_json_square(
    square: Problem[int], source_square: str, mocker: MockerFixture, tmp_path: Path
) -> Any:
    """Generate the JSON output from the square problem."""
    return get_gs_json(square, source_square, mocker, tmp_path)


def test_json_test_name_square(gs_json_square: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct test names."""
    assert set(map(lambda x: x["name"], gs_json_square["tests"])) == {
        "Test 4",
        "Test 2",
        "Test -2",
    }


def test_json_test_score_square(gs_json_square: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct score."""
    assert gs_json_square["score"] == 3


def test_json_test_visibility_square(gs_json_square: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct visibility."""
    assert set(map(lambda t: t["visibility"], gs_json_square["tests"])) == {
        "visible",
        "hidden",
    }


@pytest.fixture(name="gs_json_square_incorrect")
def fixture_gs_json_square_incorrect(
    square: Problem[int],
    source_square_incorrect: str,
    mocker: MockerFixture,
    tmp_path: Path,
) -> Any:
    """Generate the JSON output from the square problem with an incorrect submission."""
    return get_gs_json(square, source_square_incorrect, mocker, tmp_path)


def test_json_test_score_square_incorrect(gs_json_square_incorrect: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct score."""
    assert gs_json_square_incorrect["score"] == 0


def test_json_test_output_square_incorrect(gs_json_square_incorrect: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct output."""
    assert any(
        map(
            lambda t: "Checked with 2. Expected 4. Got 0 instead." in t["output"],
            gs_json_square_incorrect["tests"],
        )
    )


@pytest.fixture(name="gs_json_square_error")
def fixture_gs_json_square_error(
    square: Problem[int],
    source_square_error: str,
    mocker: MockerFixture,
    tmp_path: Path,
) -> Any:
    """Generate the JSON output from the square problem with an erroring submission."""
    return get_gs_json(square, source_square_error, mocker, tmp_path)


def test_json_test_score_square_error(gs_json_square_error: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct score."""
    assert gs_json_square_error["score"] == 0


def test_json_test_output_square_error(gs_json_square_error: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct output."""
    assert all(
        map(
            lambda t: "NameError" in t["output"],
            gs_json_square_error["tests"],
        )
    )


@pytest.fixture(name="gs_json_square_custom_name")
def fixture_gs_json_square_custom_name(
    square_custom_name: Problem[int],
    source_square: str,
    mocker: MockerFixture,
    tmp_path: Path,
) -> Any:
    """Generate the JSON output from the square problem with an erroring submission."""
    return get_gs_json(square_custom_name, source_square, mocker, tmp_path)


def test_json_test_name_square_custom_name(gs_json_square_custom_name: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct test names."""
    assert set(map(lambda x: x["name"], gs_json_square_custom_name["tests"])) == {
        "Test positive two",
        "Test minus two",
        "This is a deliberately silly name!",
    }
