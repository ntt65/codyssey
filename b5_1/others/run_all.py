#!/usr/bin/env python3
"""온라인 서점 DB - 전체 실행 및 결과 저장 스크립트."""
import sqlite3
import os
import re
from pathlib import Path

DB_PATH = "bookstore.db"
RESULTS_DIR = Path("results")

# ── 쿼리 정의 ────────────────────────────────────────────────────────────────
QUERIES = [
    ("Q01", "전체 도서를 가격 높은 순으로 조회", """
SELECT b.id, b.title, b.price, b.stock
FROM book b
ORDER BY b.price DESC
"""),
    ("Q02", "재고 30권 미만인 도서 조회 (재입고 필요 목록)", """
SELECT b.id, b.title, b.stock
FROM book b
WHERE b.stock < 30
ORDER BY b.stock ASC
"""),
    ("Q03", "최근 주문 5건 조회", """
SELECT o.id, o.member_id, o.ordered_at, o.status, o.total_amount
FROM orders o
ORDER BY o.ordered_at DESC
LIMIT 5
"""),
    ("Q04", "완료된 주문 중 결제금액 20,000원 이상인 주문", """
SELECT o.id, o.member_id, o.ordered_at, o.total_amount
FROM orders o
WHERE o.status = 'completed' AND o.total_amount >= 20000
ORDER BY o.total_amount DESC
"""),
    ("Q05", "도서와 저자, 장르 이름을 함께 조회 (INNER JOIN)", """
SELECT b.id, b.title, a.name AS author, g.name AS genre, b.price
FROM book b
INNER JOIN author a ON b.author_id = a.id
INNER JOIN genre  g ON b.genre_id  = g.id
ORDER BY b.price DESC
"""),
    ("Q06", "주문 내역과 회원 이름을 함께 조회 (INNER JOIN)", """
SELECT o.id AS order_id, m.name AS member,
       o.ordered_at, o.status, o.total_amount
FROM orders o
INNER JOIN member m ON o.member_id = m.id
ORDER BY o.ordered_at DESC
"""),
    ("Q07", "한 번도 주문한 적 없는 회원 목록 (LEFT JOIN)", """
SELECT m.id, m.name, m.email, m.joined_at
FROM member m
LEFT JOIN orders o ON m.id = o.member_id
WHERE o.id IS NULL
"""),
    ("Q08", "주문 상세 - 도서 제목, 수량, 회원 이름 포함 (3테이블 INNER JOIN)", """
SELECT o.id    AS order_id,
       m.name  AS member,
       b.title AS book,
       oi.quantity,
       oi.unit_price,
       (oi.quantity * oi.unit_price) AS subtotal
FROM order_item oi
INNER JOIN orders o ON oi.order_id = o.id
INNER JOIN member m ON o.member_id = m.id
INNER JOIN book   b ON oi.book_id  = b.id
ORDER BY o.id, b.title
"""),
    ("Q09", "회원별 완료 주문 건수와 총 결제금액 집계 (COUNT + SUM + GROUP BY)", """
SELECT m.name AS member,
       COUNT(o.id)         AS order_count,
       SUM(o.total_amount) AS total_spent
FROM member m
INNER JOIN orders o ON m.id = o.member_id
WHERE o.status = 'completed'
GROUP BY m.id, m.name
ORDER BY total_spent DESC
"""),
    ("Q10", "저자별 출판 도서 수와 평균 가격 (COUNT + AVG + GROUP BY)", """
SELECT a.name AS author,
       COUNT(b.id)            AS book_count,
       ROUND(AVG(b.price))    AS avg_price
FROM author a
INNER JOIN book b ON a.id = b.author_id
GROUP BY a.id, a.name
ORDER BY book_count DESC, avg_price DESC
"""),
    ("Q11", "장르별 도서 수와 총 재고 현황 (COUNT + SUM + GROUP BY)", """
SELECT g.name AS genre,
       COUNT(b.id)  AS book_count,
       SUM(b.stock) AS total_stock
FROM genre g
INNER JOIN book b ON g.id = b.genre_id
GROUP BY g.id, g.name
ORDER BY book_count DESC
"""),
    ("Q12", "평균 도서 가격보다 비싼 도서 목록 (서브쿼리)", """
SELECT id, title, price
FROM book
WHERE price > (SELECT AVG(price) FROM book)
ORDER BY price DESC
"""),
    ("Q13", "재고 30권 미만 도서의 가격을 5% 인하 (UPDATE)", """
UPDATE book
SET price = ROUND(price * 0.95)
WHERE stock < 30
"""),
    ("Q14", "취소 상태 주문의 주문 상세 항목 삭제 (DELETE)", """
DELETE FROM order_item
WHERE order_id IN (
    SELECT id FROM orders WHERE status = 'cancelled'
)
"""),
    ("Q15", "orders.ordered_at 컬럼에 인덱스 생성 (날짜 범위 검색 성능 개선)", """
CREATE INDEX IF NOT EXISTS idx_orders_ordered_at ON orders(ordered_at)
"""),
]

BONUS_QUERIES = [
    ("BONUS_A", "[비교 A] JOIN 방식 - 가장 많이 팔린 도서를 구매한 회원 목록", """
SELECT DISTINCT m.id, m.name, m.email
FROM member m
INNER JOIN orders     o  ON m.id  = o.member_id
INNER JOIN order_item oi ON o.id  = oi.order_id
WHERE oi.book_id = (
    SELECT book_id
    FROM order_item
    GROUP BY book_id
    ORDER BY SUM(quantity) DESC
    LIMIT 1
)
"""),
    ("BONUS_B", "[비교 B] 서브쿼리 방식 - 동일 요구, 동일 결과", """
SELECT id, name, email
FROM member
WHERE id IN (
    SELECT DISTINCT o.member_id
    FROM orders o
    INNER JOIN order_item oi ON o.id = oi.order_id
    WHERE oi.book_id = (
        SELECT book_id
        FROM order_item
        GROUP BY book_id
        ORDER BY SUM(quantity) DESC
        LIMIT 1
    )
)
"""),
    ("REPORT1", "미니 리포트 1: 월별 주문 건수 및 총 매출 추이", """
SELECT strftime('%Y-%m', ordered_at) AS month,
       COUNT(id)                      AS order_count,
       SUM(total_amount)              AS monthly_revenue
FROM orders
WHERE status = 'completed'
GROUP BY month
ORDER BY month
"""),
    ("REPORT2", "미니 리포트 2: 가장 많이 팔린 도서 TOP 5", """
SELECT b.title,
       a.name                           AS author,
       SUM(oi.quantity)                 AS total_sold,
       SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM order_item oi
INNER JOIN book   b ON oi.book_id  = b.id
INNER JOIN author a ON b.author_id = a.id
GROUP BY b.id, b.title, a.name
ORDER BY total_sold DESC
LIMIT 5
"""),
    ("REPORT3", "미니 리포트 3: 구매 금액 기준 상위 회원 TOP 3 (VIP)", """
SELECT m.name,
       m.email,
       COUNT(o.id)         AS order_count,
       SUM(o.total_amount) AS lifetime_value
FROM member m
INNER JOIN orders o ON m.id = o.member_id
WHERE o.status = 'completed'
GROUP BY m.id, m.name, m.email
ORDER BY lifetime_value DESC
LIMIT 3
"""),
]

FK_ERROR_TESTS = [
    ("존재하지 않는 book_id(999)로 order_item INSERT",
     "INSERT INTO order_item (order_id, book_id, quantity, unit_price) VALUES (1, 999, 1, 10000)"),
    ("존재하지 않는 member_id(999)로 orders INSERT",
     "INSERT INTO orders (member_id, ordered_at, status, total_amount) VALUES (999, '2024-06-01 10:00:00', 'pending', 15000)"),
]


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def connect(path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def run_script(conn: sqlite3.Connection, path: str) -> None:
    with open(path, encoding="utf-8") as f:
        conn.executescript(f.read())


def fmt_table(rows) -> str:
    if not rows:
        return "(결과 없음)\n"
    headers = list(rows[0].keys())
    data = [[str(v) if v is not None else "NULL" for v in r] for r in rows]
    widths = [len(h) for h in headers]
    for row in data:
        for i, v in enumerate(row):
            widths[i] = max(widths[i], len(v))
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    hdr = "|" + "|".join(f" {h:<{w}} " for h, w in zip(headers, widths)) + "|"
    lines = [sep, hdr, sep]
    for row in data:
        lines.append("|" + "|".join(f" {v:<{w}} " for v, w in zip(row, widths)) + "|")
    lines.append(sep)
    lines.append(f"({len(rows)} rows)")
    return "\n".join(lines)


def run_one(conn: sqlite3.Connection, label: str, desc: str, sql: str, out_path: Path) -> None:
    stmt = sql.strip()
    upper = stmt.upper()
    lines = [
        "=" * 60,
        f"{label}. {desc}",
        "=" * 60,
        "",
        "[SQL]",
        stmt,
        "",
        "[결과]",
    ]
    try:
        if upper.startswith("SELECT"):
            rows = conn.execute(stmt).fetchall()
            lines.append(fmt_table(rows))
        elif upper.startswith("UPDATE"):
            cur = conn.execute(stmt)
            conn.commit()
            # 변경 후 확인 SELECT
            tbl = re.search(r"UPDATE\s+(\w+)", stmt, re.IGNORECASE).group(1)
            after = conn.execute(f"SELECT * FROM {tbl} ORDER BY id").fetchall()
            lines.append(f"UPDATE 완료 - {cur.rowcount}행 변경됨")
            lines.append("\n[변경 후 테이블 상태]")
            lines.append(fmt_table(after))
        elif upper.startswith("DELETE"):
            cur = conn.execute(stmt)
            conn.commit()
            lines.append(f"DELETE 완료 - {cur.rowcount}행 삭제됨")
        elif upper.startswith("CREATE INDEX"):
            conn.execute(stmt)
            conn.commit()
            lines.append("인덱스 생성 완료")
            idx = conn.execute(
                "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            lines.append(fmt_table(idx))
        else:
            conn.executescript(stmt)
            lines.append("실행 완료")
    except Exception as e:
        lines.append(f"[오류] {e}")

    result = "\n".join(lines) + "\n"
    print(result)
    out_path.write_text(result, encoding="utf-8")


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    # DB 초기화
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    RESULTS_DIR.mkdir(exist_ok=True)
    bonus_dir = RESULTS_DIR / "bonus"
    bonus_dir.mkdir(exist_ok=True)

    conn = connect()
    print("▶ 스키마 생성...")
    run_script(conn, "schema.sql")

    print("▶ 샘플 데이터 입력...")
    run_script(conn, "data.sql")
    print("  완료\n")

    # ── 핵심 쿼리 15개
    print("▶ 핵심 쿼리 실행\n")
    for label, desc, sql in QUERIES:
        print(f"  → {label}")
        run_one(conn, label, desc, sql.strip(), RESULTS_DIR / f"{label}_result.txt")

    # ── 보너스: JOIN vs 서브쿼리 + 리포트
    print("\n▶ 보너스 쿼리 실행\n")
    for label, desc, sql in BONUS_QUERIES:
        print(f"  → {label}")
        run_one(conn, label, desc, sql.strip(), bonus_dir / f"{label}_result.txt")

    # ── 보너스: FK 에러 (인메모리 DB에서 안전하게 테스트)
    print("\n▶ FK 에러 시도 (인메모리 DB)\n")
    fk_conn = sqlite3.connect(":memory:")
    fk_conn.execute("PRAGMA foreign_keys = ON")
    fk_conn.row_factory = sqlite3.Row
    with open("schema.sql", encoding="utf-8") as f:
        fk_conn.executescript(f.read())
    with open("data.sql", encoding="utf-8") as f:
        fk_conn.executescript(f.read())

    fk_lines = ["=" * 60, "BONUS_FK. FK 제약 위반 시도 및 오류 분석", "=" * 60, ""]
    for desc, stmt in FK_ERROR_TESTS:
        fk_lines += [f"[시도] {desc}", f"[SQL] {stmt}", ""]
        try:
            fk_conn.execute(stmt)
            fk_conn.commit()
            fk_lines.append("[결과] INSERT 성공 (예상치 못한 결과)\n")
        except Exception as e:
            fk_lines.append(f"[결과] FK 오류 발생: {e}")
            fk_lines.append("  → FK 제약이 정상 동작합니다.\n")
    fk_lines += [
        "── 분석 ────────────────────────────────────────────",
        "PRAGMA foreign_keys = ON 설정 시 SQLite는 참조 무결성을 강제한다.",
        "부모 테이블에 없는 PK를 FK로 지정하면 INSERT가 거부된다.",
        "수정 방법: 먼저 부모 테이블에 해당 행을 추가하거나",
        "           존재하는 PK 값을 사용한다.",
    ]
    fk_result = "\n".join(fk_lines) + "\n"
    print(fk_result)
    (bonus_dir / "BONUS_FK_result.txt").write_text(fk_result, encoding="utf-8")

    conn.close()
    fk_conn.close()
    print(f"\n완료. 결과 파일: {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
