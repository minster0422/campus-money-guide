from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.sch_notices import fetch_opportunities, validate_output


def main() -> int:
    parser = argparse.ArgumentParser(description="순천향대학교 경제기회 공고를 수집합니다.")
    parser.add_argument("--pages", type=int, default=3, help="게시판별로 확인할 페이지 수")
    parser.add_argument("--dry-run", action="store_true", help="파일을 덮어쓰지 않고 결과만 확인")
    args = parser.parse_args()

    frame, meta = fetch_opportunities(pages_per_board=max(args.pages, 1))
    errors = validate_output(frame)
    if errors:
        for error in errors:
            print(f"[오류] {error}")
        return 1

    print(frame[["category", "title", "deadline", "organization"]].to_string(index=False))
    print(f"\n총 {len(frame)}건 · 수집 시각 {meta['fetched_at']}")
    if args.dry_run:
        print("dry-run이므로 기존 데이터는 변경하지 않았습니다.")
        return 0

    data_dir = ROOT / "data"
    frame.to_csv(data_dir / "opportunities.csv", index=False, encoding="utf-8-sig")
    (data_dir / "opportunities_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("data/opportunities.csv와 메타데이터를 갱신했습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

