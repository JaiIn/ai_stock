"""Print a safe read-only audit of the local snapshot SQLite file."""

import json

from ai_stock.storage.local_snapshot_db_audit import (
    audit_local_snapshot_db_readonly,
)


def main() -> int:
    result = audit_local_snapshot_db_readonly()
    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Local snapshot DB read-only audit.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
