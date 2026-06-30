"""Run the approved fake snapshot smoke against one local SQLite file."""

import json
from pathlib import Path

from ai_stock.storage.local_snapshot_db_smoke import (
    PLANNED_DB_RELATIVE_PATH,
    run_fake_snapshot_local_db_file_smoke,
)


def main() -> int:
    """Execute the fixed no-network smoke once and print safe diagnostics."""

    database_path = Path(PLANNED_DB_RELATIVE_PATH)
    try:
        result = run_fake_snapshot_local_db_file_smoke(database_path)
    except Exception as exc:
        print("[FAIL] Fake snapshot local SQLite file smoke.")
        print(
            json.dumps(
                {
                    "success": False,
                    "phase": "fake_snapshot_local_db_file_smoke",
                    "safe_error_type": type(exc).__name__,
                    "safe_message": "Local SQLite file smoke did not complete.",
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 1

    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Fake snapshot local SQLite file smoke.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
