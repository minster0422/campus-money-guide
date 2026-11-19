from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://home.sch.ac.kr"


@dataclass(frozen=True)
class Board:
    name: str
    url: str
    board_no: str


BOARDS = (
    Board(
        name="장학공지",
        url=f"{BASE_URL}/sch/06/010300.jsp",
        board_no="20090724142604517617",
    ),
    Board(
        name="대학공지",
        url=f"{BASE_URL}/sch/06/010100.jsp",
        board_no="20090723152156588979",
    ),
)

OUTPUT_COLUMNS = [
    "id",
    "title",
    "category",
    "organization",
    "eligible_grades",
    "residence",
    "weekly_hours",
    "benefit_type",
    "amount_min",
    "amount_max",
    "amount_note",
    "deadline",
    "duration",
    "competition",
    "summary",
    "source_url",
    "tags",
]

INCLUDE_KEYWORDS = (
    "장학",
    "근로",
    "인턴",
    "공모",
    "경진",
    "대회",
    "서포터즈",
    "튜터",
    "멘토",
    "홍보대사",
    "활동비",
    "지원금",
    "상금",
    "층장",
)
ACTION_KEYWORDS = ("신청", "모집", "선발", "접수", "공모", "경진", "대회")
EXCLUDE_KEYWORDS = (
    "근로기관용",
    "수요조사",
    "사전교육",
    "중복지원 방지",
    "부정수급",
    "선발 기준 안내",
    "채용공고",
    "방청 심사위원",
)
DEADLINE_LABELS = (
    "신청기간",
    "신청 기간",
    "접수기간",
    "접수 기간",
    "모집기간",
    "모집 기간",
    "지원기간",
    "지원 기간",
    "제출기간",
    "제출 기간",
    "제출기한",
    "제출 기한",
    "추천기한",
    "추천 기한",
    "모집기한",
    "모집 기한",
    "신청기한",
    "신청 마감",
    "접수 마감",
    "마감일",
)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def is_relevant_title(title: str) -> bool:
    normalized = _clean_text(title)
    if any(keyword in normalized for keyword in EXCLUDE_KEYWORDS):
        return False
    return any(keyword in normalized for keyword in INCLUDE_KEYWORDS) and any(
        keyword in normalized for keyword in ACTION_KEYWORDS
    )


def classify_title(title: str) -> tuple[str, str, str, str]:
    if "근로" in title or "인턴" in title:
        return "교내근로", "근로장학금", "근로형", "근로|장학"
    if "공모" in title:
        return "공모전", "상금·혜택", "경쟁형", "공모전|상금"
    if "경진" in title or "대회" in title:
        return "경진대회", "상금·혜택", "경쟁형", "경진대회|상금"
    if "튜터" in title or "멘토" in title:
        return "튜터링", "활동비·장학금", "선발형", "튜터링|멘토링"
    if "서포터즈" in title or "홍보대사" in title:
        return "서포터즈", "활동비·혜택", "선발형", "서포터즈|활동비"
    if "층장" in title:
        return "생활관", "활동비·비용감면", "선발형", "생활관|기숙사"
    return "장학금", "장학금", "선발형", "장학금|생활비"


def _won_value(raw: str, unit: str) -> int:
    value = int(raw.replace(",", ""))
    return value * 10_000 if "만" in unit else value


def extract_amount_info(category: str, body: str) -> tuple[int, int, str]:
    normalized = _clean_text(body.replace("\xa0", " "))

    if category == "교내근로":
        wages = [
            int(value.replace(",", ""))
            for value in re.findall(r"(?:시간당|시급)\s*([\d,]+)\s*원", normalized)
        ]
        wages = [value for value in wages if 5_000 <= value <= 100_000]
        if wages:
            low, high = min(wages), max(wages)
            note = f"시급 {low:,}원" if low == high else f"시급 {low:,}원 ~ {high:,}원"
            return 0, 0, note
        return 0, 0, ""

    values: list[int] = []
    if category in {"장학금", "튜터링", "서포터즈", "생활관"}:
        patterns = (
            r"장학금\s+([\d,]+)\s*(만\s*원|원)",
            r"지원금액.{0,40}?([\d,]+)\s*(만\s*원|원)",
            r"활동비\s+([\d,]+)\s*(만\s*원|원)",
        )
    else:
        patterns = (
            r"(?:대상|최우수상|우수작|우수상|장려작|장려상).{0,30}?([\d,]+)\s*(만\s*원|원)",
        )

    for pattern in patterns:
        for raw, unit in re.findall(pattern, normalized):
            value = _won_value(raw, unit.replace(" ", ""))
            if 10_000 <= value <= 100_000_000:
                values.append(value)

    if not values:
        return 0, 0, ""
    low, high = min(values), max(values)
    note = f"{low:,}원" if low == high else f"{low:,}원 ~ {high:,}원"
    if category in {"공모전", "경진대회"}:
        note = f"수상 시 {note}"
    return low, high, note


def extract_eligible_grades(body: str) -> str:
    normalized = _clean_text(body.replace("\xa0", " "))
    for start, end in re.findall(r"(?<!\d)([1-4])\s*[~∼-]\s*([1-4])\s*학년", normalized):
        first, last = int(start), int(end)
        if first <= last:
            return "|".join(str(value) for value in range(first, last + 1))
    return "1|2|3|4"


def _year_for_month(month: int, published: date) -> int:
    # December notices often recruit for the following January.
    return published.year + 1 if month + 2 < published.month else published.year


def _last_date_in_text(text: str, published: date) -> date | None:
    normalized = text.replace("．", ".").replace("／", "/").replace("～", "~")
    candidates: list[date] = []

    for match in re.finditer(r"(20\d{2})\s*[.년/-]\s*(\d{1,2})\s*[.월/-]\s*(\d{1,2})", normalized):
        try:
            candidates.append(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
        except ValueError:
            continue

    range_pattern = re.compile(
        r"(?<!\d)(\d{1,2})\s*[./월]\s*(\d{1,2})\s*(?:일)?\s*~\s*"
        r"(?:(\d{1,2})\s*[./월]\s*)?(\d{1,2})\s*(?:일)?"
    )
    for match in range_pattern.finditer(normalized):
        end_month = int(match.group(3) or match.group(1))
        end_day = int(match.group(4))
        try:
            candidates.append(date(_year_for_month(end_month, published), end_month, end_day))
        except ValueError:
            continue

    for match in re.finditer(r"[~∼]\s*(\d{1,2})\s*[./월]\s*(\d{1,2})\s*(?:일)?", normalized):
        month, day = int(match.group(1)), int(match.group(2))
        try:
            candidates.append(date(_year_for_month(month, published), month, day))
        except ValueError:
            continue

    for match in re.finditer(r"(?<!\d)(\d{1,2})\s*월\s*(\d{1,2})\s*일", normalized):
        month, day = int(match.group(1)), int(match.group(2))
        try:
            candidates.append(date(_year_for_month(month, published), month, day))
        except ValueError:
            continue

    return max(candidates) if candidates else None


def extract_deadline(title: str, body: str, published: date) -> date | None:
    title_deadline = _last_date_in_text(title, published)
    if title_deadline:
        return title_deadline

    lines = [line.strip() for line in body.splitlines() if line.strip()]
    labeled_indexes = [
        index
        for index, line in enumerate(lines)
        if any(label in line for label in DEADLINE_LABELS)
    ]
    for index in labeled_indexes:
        deadline = _last_date_in_text(lines[index], published)
        if not deadline and index + 1 < len(lines):
            deadline = _last_date_in_text(lines[index + 1], published)
        if deadline:
            return deadline
    return None


def parse_board_list(html: str, board: Board) -> list[dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, object]] = []
    for row in soup.select("div.board_list table.type_board tbody tr"):
        link = row.select_one("td.subject a[href]")
        date_cell = row.select_one("td.date")
        writer_cell = row.select_one("td.writer")
        if not link or not date_cell:
            continue
        title = _clean_text(link.get_text(" ", strip=True))
        if not is_relevant_title(title):
            continue
        published = pd.to_datetime(_clean_text(date_cell.get_text(" ", strip=True)).replace("날짜:", ""), errors="coerce")
        if pd.isna(published):
            continue
        source_url = urljoin(board.url, link.get("href", ""))
        article_match = re.search(r"article_no=(\d+)", source_url)
        article_no = article_match.group(1) if article_match else hashlib.sha1(source_url.encode()).hexdigest()[:16]
        organization = (
            _clean_text(_clean_text(writer_cell.get_text(" ", strip=True)).replace("작성자:", ""))
            if writer_cell
            else board.name
        )
        records.append(
            {
                "article_no": article_no,
                "title": title,
                "organization": organization,
                "published": published.date(),
                "source_url": source_url,
                "board_name": board.name,
            }
        )
    return records


def parse_detail_body(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    body = soup.select_one("div.board_contents")
    if not body:
        return ""
    return body.get_text("\n", strip=True).replace("\\n", "\n")


def normalize_notice(record: dict[str, object], body: str) -> dict[str, object]:
    title = str(record["title"])
    published = record["published"]
    if not isinstance(published, date):
        published = pd.Timestamp(published).date()
    category, benefit_type, competition, tags = classify_title(title)
    deadline = extract_deadline(title, body, published)
    amount_min, amount_max, amount_note = extract_amount_info(category, body)
    summary = (
        f"순천향대학교 {record['board_name']}에서 수집한 공식 공고입니다. "
        "금액과 세부 지원 조건은 원문에서 확인하세요."
    )
    return {
        "id": f"sch-{record['article_no']}",
        "title": title,
        "category": category,
        "organization": record["organization"],
        "eligible_grades": extract_eligible_grades(body),
        "residence": "전체",
        "weekly_hours": 0,
        "benefit_type": benefit_type,
        "amount_min": amount_min,
        "amount_max": amount_max,
        "amount_note": amount_note,
        "deadline": deadline.isoformat() if deadline else "",
        "duration": "공고 원문 확인",
        "competition": competition,
        "summary": summary,
        "source_url": record["source_url"],
        "tags": tags,
    }


def fetch_opportunities(
    *,
    pages_per_board: int = 3,
    max_age_days: int = 90,
    unknown_deadline_max_age_days: int = 14,
    today: date | None = None,
    timeout: int = 20,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    today = today or date.today()
    client = session or requests.Session()
    client.headers.update({"User-Agent": "CampusMoneyGuide/1.0 (student project)"})
    raw_records: list[dict[str, object]] = []

    for board in BOARDS:
        for page in range(max(pages_per_board, 1)):
            response = client.get(
                board.url,
                params={"mode": "list", "board_no": board.board_no, "pager.offset": page * 10},
                timeout=timeout,
            )
            response.raise_for_status()
            raw_records.extend(parse_board_list(response.content.decode("utf-8", errors="replace"), board))

    normalized: list[dict[str, object]] = []
    cutoff = today - timedelta(days=max_age_days)
    seen: set[str] = set()
    for record in raw_records:
        article_no = str(record["article_no"])
        if article_no in seen or record["published"] < cutoff:
            continue
        seen.add(article_no)
        response = client.get(str(record["source_url"]), timeout=timeout)
        response.raise_for_status()
        item = normalize_notice(
            record,
            parse_detail_body(response.content.decode("utf-8", errors="replace")),
        )
        deadline = pd.to_datetime(item["deadline"], errors="coerce")
        if pd.notna(deadline) and deadline.date() < today:
            continue
        if pd.isna(deadline) and record["published"] < today - timedelta(days=unknown_deadline_max_age_days):
            continue
        normalized.append(item)

    frame = pd.DataFrame(normalized, columns=OUTPUT_COLUMNS)
    if not frame.empty:
        deadline_sort = pd.to_datetime(frame["deadline"], errors="coerce")
        frame = (
            frame.assign(_deadline_sort=deadline_sort)
            .sort_values(["_deadline_sort", "category"], na_position="last")
            .drop(columns="_deadline_sort")
            .reset_index(drop=True)
        )

    meta = {
        "source_type": "official_school_notices",
        "school": "순천향대학교",
        "fetched_at": datetime.now().astimezone().isoformat(timespec="minutes"),
        "count": int(len(frame)),
        "sources": [{"name": board.name, "url": board.url} for board in BOARDS],
    }
    return frame, meta


def validate_output(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    missing_columns = [column for column in OUTPUT_COLUMNS if column not in frame.columns]
    if missing_columns:
        errors.append(f"필수 열 누락: {', '.join(missing_columns)}")
    if frame.empty:
        errors.append("수집된 경제기회가 없습니다.")
    if not frame.empty and frame["source_url"].duplicated().any():
        errors.append("중복된 원문 링크가 있습니다.")
    return errors

