"""Print the safe latest snapshot read model from the local SQLite file."""

import json

from ai_stock.storage.local_snapshot_latest_read_model import (
    build_local_snapshot_latest_read_model,
)


def main() -> int:
    result = build_local_snapshot_latest_read_model()
    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Local snapshot latest read model.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
