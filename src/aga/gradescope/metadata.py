# pylint: disable=invalid-name,too-many-instance-attributes
# These are mandated by the json schema
"""Parses Gradescope's `submission_metadata.json` file."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from backports.datetime_fromisoformat import MonkeyPatch
from dataclasses_json import config, dataclass_json
from marshmallow import fields

from .runner import GradescopeJson

# backwards compatibility for python 3.6
MonkeyPatch.patch_fromisoformat()


@dataclass_json
@dataclass(frozen=True)
class GradescopeAssignmentMetadata:
    """The JSON schema for Gradescope's assignment settings.

    Attributes
    ----------
    due_date : datetime
        The assignment's due date.
    group_size : Optional[int]
        The maximum group size on a group assignment.
    group_submission : bool
        Whether group submission is allowed.
    id : int
        The assignment's ID.
    course_id : int
        The course's ID.
    late_due_date : Optional[datetime]
        The late due date, or None if late submission disallowed.
    release_date : datetime
        The assignment's release date.
    title : str
        The assignment's title.
    total_points : float
        The total point value of the assignment.
    """

    due_date: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,  # type: ignore
            mm_field=fields.DateTime(format="iso"),
        )
    )
    group_size: Optional[int]
    group_submission: bool
    id: int
    course_id: int
    late_due_date: Optional[datetime]
    release_date: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,  # type: ignore
            mm_field=fields.DateTime(format="iso"),
        )
    )
    title: str
    total_points: float = field(metadata=config(encoder=str, decoder=float))


@dataclass_json
@dataclass(frozen=True)
class GradescopeAssignmentUser:
    """The JSON schema for a 'user' (submitter) of a Gradescope assignment.

    Attributes
    ----------
    email : str
        The submitter's email.
    id : int
        The submitter's ID.
    name : str
        The submitter's name.
    """

    email: str
    id: int
    name: str


@dataclass_json
@dataclass(frozen=True)
class GradescopePreviousSubmission:
    """The JSON schema for a previous submission record.

    Attributes
    ----------
    submission_time : datetime
        The time of the previous submission.
    score : float
        The previous submission's score.
    results : GradescopeJson
        The results.json file from the previous submission.
    """

    submission_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,  # type: ignore
            mm_field=fields.DateTime(format="iso"),
        )
    )
    score: float
    results: GradescopeJson


@dataclass_json
@dataclass(frozen=True)
class GradescopeSubmissionMetadata:
    """The JSON schema for Gradescope's submission metadata.

    Documentation online here
    <https://gradescope-autograders.readthedocs.io/en/latest/submission_metadata/>.

    Attributes
    ----------
    id : int
        A unique submission identifier.
    created_at : datetime
        The submission time.
    assignment : GradescopeAssignmentMetadata
        The assignment's specific settings.
    submission_method : str
        One of "upload", "GitHub", or "Bitbucket"
    users : List[GradescopeAssignmentUser]
        The people who submitted the assignment. Multiple if the assignment is a group
        assignment.
    previous_submissions : List[GradescopePreviousSubmission]
        The previous submissions.
    """

    id: int
    created_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,  # type: ignore
            mm_field=fields.DateTime(format="iso"),
        )
    )
    assignment: GradescopeAssignmentMetadata
    submission_method: str
    users: List[GradescopeAssignmentUser]
    previous_submissions: List[GradescopePreviousSubmission]


def load_submission_metadata_from_file(path: str) -> GradescopeSubmissionMetadata:
    """Load the submission metadata from a json file."""
    with open(path, encoding="UTF-8") as file:
        # pylint: disable=no-member
        return GradescopeSubmissionMetadata.from_json(file.read())  # type: ignore
