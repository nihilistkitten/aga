"""Contains a TestResult and TestRunner for producing gradescope's results.json file.

The design of this module is inspire by gradescope_utils's JSONTestRunner, but this is a
complete rewrite.
"""

from dataclasses import dataclass
from typing import Any, List, Optional, TextIO
from unittest import TestResult, TestSuite

from dataclasses_json import dataclass_json

from ..core import AgaTestCase


@dataclass_json
@dataclass
class _GradescopeTestJson:
    """The JSON schema for a single Test.

    Attributes
    ----------
    score : Optional[float]
        The test's score. Required if no top-level score is set.
    max_score : Optional[float]
        The max score for the test.
    name : Optional[str]
        The test's name.
    output : Optional[str]
        Human-readable text output of the test.
    tags : Optional[List[str]]
        Tags for the test.
    visibility : str
        The test's visibility. "hidden", "visible", "after_due_date", "after_published"
    """

    score: Optional[float] = None
    max_score: Optional[float] = None
    name: Optional[str] = None
    number: Optional[float] = None
    output: Optional[str] = None
    tags: Optional[str] = None
    visibility: Optional[str] = None


@dataclass_json
@dataclass
class GradescopeJson:
    """The JSON schema for Gradescope.

    We currently don't support the leaderboard and extra_data features of the gradescope
    schema. Those are documented on the autograder documentation, here:
    <https://gradescope-autograders.readthedocs.io/en/latest/specs/>.

    Attributes
    ----------
    tests : List[_GradescopeJsonTest]
        The tests for the problem. Required if no global score provided.
    score : Optional[float]
        The overall score. Required if any test has no set score.
    execution_time : Optional[int]
        The execution time of all the tests, in seconds.
    output : Optional[str]
        The top-level, human-readable text output for all the problems.
    visibility : Optional[str]
        The default visibility for each test. Overridden by test-specific settings.
    stdout_visibility : Optional[str]
        Whether to show stdout for the tests. Same options as for visibility.
    """

    tests: List[_GradescopeTestJson]
    score: Optional[float] = None
    execution_time: Optional[int] = None
    output: Optional[str] = None
    visibility: Optional[str] = None
    stdout_visibility: Optional[str] = None


class _GradescopeTestResult(TestResult):
    """A custom `TestResult` that constructs the gradescope json object for the test.

    This is _not_ safe to be used in place of an arbitrary TestResult. This is because
    it relies on specific methods of the `AgaTestCase` class. It should only be used
    with TestSuites that we _know_ only containt `AgaTestCase`s.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._json = GradescopeJson(tests=[])

    @staticmethod
    def _visibility_string(hidden: bool) -> str:
        """Get the appropriate visibility string for Gradescope's JSON format."""
        return "hidden" if hidden else "visible"

    def _test_json(self, test: AgaTestCase) -> _GradescopeTestJson:
        """Construct the test json schema for a test, with _no_ output."""
        metadata = test.metadata()
        visibility = self._visibility_string(metadata.hidden)

        return _GradescopeTestJson(
            max_score=1.0,
            name=metadata.name,
            score=metadata.max_score,
            visibility=visibility,
        )

    def _err_json(self, test: AgaTestCase, err) -> _GradescopeTestJson:  # type: ignore
        """Construct the test json schema for an error."""
        json = self._test_json(test)
        json.output = f"Test failed: {err}."
        json.score = 0.0

        return json

    # lots of type: ignores because these methods all restrict the input TestCase type

    def addError(self, test: AgaTestCase, err) -> None:  # type: ignore
        """Add an error."""
        super().addError(test, err)
        self._json.tests.append(self._err_json(test, err))

    def addFailure(self, test: AgaTestCase, err) -> None:  # type: ignore
        """Add a failure."""
        super().addFailure(test, err)
        self._json.tests.append(self._err_json(test, err))

    def addSuccess(self, test: AgaTestCase) -> None:  # type: ignore[override]
        """Add a success."""
        super().addSuccess(test)
        self._json.tests.append(self._test_json(test))

    def build(self) -> str:
        """Build the result into a JSON string."""
        self._json.score = sum(t.score for t in self._json.tests)

        # pylint: disable=no-member
        return self._json.to_json()  # type: ignore


def run_suite(suite: TestSuite, stream: TextIO) -> None:
    """Run a TestSuite of `AgaTestCase`s, writing json to a text stream."""
    result: _GradescopeTestResult = suite.run(_GradescopeTestResult())  # type: ignore
    stream.write(result.build())
