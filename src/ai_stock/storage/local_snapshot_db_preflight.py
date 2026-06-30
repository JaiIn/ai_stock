"""No-I/O safety contract for a future local snapshot SQLite file.

This module only builds and validates immutable metadata. It does not inspect
the filesystem, load configuration, open SQLite, initialize schema, construct
repositories, or send network requests.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath

STAGE = "MS-06.05"
STORAGE_MODE = "local_sqlite_file_preflight"
PLANNED_DB_RELATIVE_PATH = "data/local/ai_stock.sqlite3"
REQUIRED_IGNORE_PATTERNS = ("data/", "*.sqlite", "*.sqlite3", "*.db")

_FORBIDDEN_CREDENTIAL_FILE_NAMES = {
    ".env",
    ".env.local",
    "credentials",
    "credentials.json",
    "secrets",
    "secrets.json",
}
_FORBIDDEN_CREDENTIAL_TERMS = ("credential", "secret", "token")


@dataclass(frozen=True, slots=True)
class LocalSnapshotDbFilePreflightPlan:
    """Immutable policy for a later, separately approved file DB stage."""

    stage: str
    storage_mode: str
    planned_db_relative_path: str
    db_file_creation_allowed_this_stage: bool
    actual_db_file_created: bool
    data_directory_creation_allowed: bool
    schema_initialization_allowed: bool
    repository_file_connection_allowed: bool
    git_ignore_required: bool
    required_ignore_patterns: tuple[str, ...]
    api_call_allowed: bool
    oauth_token_endpoint_allowed: bool
    live_smoke_execution_allowed: bool
    env_file_read_allowed: bool
    credential_required: bool
    account_seq_allowed: bool
    real_order_related_call_allowed: bool


@dataclass(frozen=True, slots=True)
class LocalSnapshotDbFilePreflightResult:
    """Safe validation result derived only from caller-supplied observations."""

    planned_path_is_expected: bool
    planned_path_is_repo_relative: bool
    planned_path_is_credential_path: bool
    db_file_creation_disabled: bool
    actual_db_file_absent: bool
    git_ignore_policy_satisfied: bool
    missing_ignore_patterns: tuple[str, ...]
    external_actions_disabled: bool
    preflight_contract_valid: bool
    ready_for_file_db_creation: bool
    actual_db_file_created: bool
    safe_message: str


def build_local_snapshot_db_file_preflight() -> LocalSnapshotDbFilePreflightPlan:
    """Build the fixed MS-06.05 plan without filesystem or external I/O."""

    return LocalSnapshotDbFilePreflightPlan(
        stage=STAGE,
        storage_mode=STORAGE_MODE,
        planned_db_relative_path=PLANNED_DB_RELATIVE_PATH,
        db_file_creation_allowed_this_stage=False,
        actual_db_file_created=False,
        data_directory_creation_allowed=False,
        schema_initialization_allowed=False,
        repository_file_connection_allowed=False,
        git_ignore_required=True,
        required_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
        api_call_allowed=False,
        oauth_token_endpoint_allowed=False,
        live_smoke_execution_allowed=False,
        env_file_read_allowed=False,
        credential_required=False,
        account_seq_allowed=False,
        real_order_related_call_allowed=False,
    )


def validate_local_snapshot_db_file_preflight(
    plan: LocalSnapshotDbFilePreflightPlan,
    *,
    observed_ignore_patterns: Iterable[str],
    actual_db_file_exists: bool,
) -> LocalSnapshotDbFilePreflightResult:
    """Validate the plan using explicit observations without performing I/O."""

    normalized_path = plan.planned_db_relative_path.replace("\\", "/")
    planned_path = PurePosixPath(normalized_path)
    planned_path_is_expected = normalized_path == PLANNED_DB_RELATIVE_PATH
    planned_path_is_repo_relative = (
        not planned_path.is_absolute()
        and ".." not in planned_path.parts
        and planned_path.parts[:2] == ("data", "local")
    )
    planned_path_is_credential_path = _is_credential_path(planned_path)

    observed_patterns = {
        pattern.strip()
        for pattern in observed_ignore_patterns
        if pattern and pattern.strip()
    }
    missing_ignore_patterns = tuple(
        pattern
        for pattern in plan.required_ignore_patterns
        if pattern not in observed_patterns
    )
    git_ignore_policy_satisfied = (
        plan.git_ignore_required
        and plan.required_ignore_patterns == REQUIRED_IGNORE_PATTERNS
        and not missing_ignore_patterns
    )

    db_file_creation_disabled = all(
        value is False
        for value in (
            plan.db_file_creation_allowed_this_stage,
            plan.actual_db_file_created,
            plan.data_directory_creation_allowed,
            plan.schema_initialization_allowed,
            plan.repository_file_connection_allowed,
        )
    )
    actual_db_file_absent = actual_db_file_exists is False
    external_actions_disabled = all(
        value is False
        for value in (
            plan.api_call_allowed,
            plan.oauth_token_endpoint_allowed,
            plan.live_smoke_execution_allowed,
            plan.env_file_read_allowed,
            plan.credential_required,
            plan.account_seq_allowed,
            plan.real_order_related_call_allowed,
        )
    )
    preflight_contract_valid = all(
        (
            plan.stage == STAGE,
            plan.storage_mode == STORAGE_MODE,
            planned_path_is_expected,
            planned_path_is_repo_relative,
            not planned_path_is_credential_path,
            db_file_creation_disabled,
            actual_db_file_absent,
            git_ignore_policy_satisfied,
            external_actions_disabled,
        )
    )

    if preflight_contract_valid:
        safe_message = (
            "Local SQLite file preflight is valid; file creation remains disabled."
        )
    else:
        safe_message = (
            "Local SQLite file preflight is not ready; file creation remains disabled."
        )

    return LocalSnapshotDbFilePreflightResult(
        planned_path_is_expected=planned_path_is_expected,
        planned_path_is_repo_relative=planned_path_is_repo_relative,
        planned_path_is_credential_path=planned_path_is_credential_path,
        db_file_creation_disabled=db_file_creation_disabled,
        actual_db_file_absent=actual_db_file_absent,
        git_ignore_policy_satisfied=git_ignore_policy_satisfied,
        missing_ignore_patterns=missing_ignore_patterns,
        external_actions_disabled=external_actions_disabled,
        preflight_contract_valid=preflight_contract_valid,
        ready_for_file_db_creation=False,
        actual_db_file_created=not actual_db_file_absent,
        safe_message=safe_message,
    )


def _is_credential_path(path: PurePosixPath) -> bool:
    lowered_parts = tuple(part.casefold() for part in path.parts)
    if any(part in _FORBIDDEN_CREDENTIAL_FILE_NAMES for part in lowered_parts):
        return True
    return any(
        term in part
        for part in lowered_parts
        for term in _FORBIDDEN_CREDENTIAL_TERMS
    )
