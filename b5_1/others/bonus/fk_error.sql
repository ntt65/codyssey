-- ================================================================
-- 보너스 2: 데이터 정합성 깨뜨려 보기 - FK 에러 시도
-- (run_all.py 가 인메모리 DB에서 실행 후 결과를 results/bonus/ 에 저장)
-- ================================================================

PRAGMA foreign_keys = ON;

-- 시도 1: 존재하지 않는 book_id(999)로 order_item INSERT
-- 예상 결과: FOREIGN KEY constraint failed
INSERT INTO order_item (order_id, book_id, quantity, unit_price)
VALUES (1, 999, 1, 10000);

-- 시도 2: 존재하지 않는 member_id(999)로 orders INSERT
-- 예상 결과: FOREIGN KEY constraint failed
INSERT INTO orders (member_id, ordered_at, status, total_amount)
VALUES (999, '2024-06-01 10:00:00', 'pending', 15000);

-- ── 왜 막히는가? ─────────────────────────────────────────────────
-- PRAGMA foreign_keys = ON 을 설정하면 SQLite가 FK 제약을 검사한다.
-- book_id=999 는 book 테이블에 없으므로 참조 무결성 위반으로 거부된다.
-- member_id=999 도 마찬가지로 member 테이블에 없어 거부된다.
--
-- 수정 방법:
--   1) 먼저 부모 테이블(book / member)에 해당 행을 INSERT한다.
--   2) 또는 존재하는 PK 값을 사용한다.
