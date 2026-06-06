PRAGMA foreign_keys = ON;

-- ================================================================
-- 온라인 서점 DB - 핵심 쿼리 15개
-- DB: SQLite | 파일: bookstore.db
-- ================================================================

-- ── 기본 조회 Q01~Q04 ────────────────────────────────────────────

-- [Q01] 전체 도서를 가격 높은 순으로 조회
SELECT b.id, b.title, b.price, b.stock
FROM book b
ORDER BY b.price DESC;

-- [Q02] 재고 30권 미만인 도서 조회 (재입고 필요 목록)
SELECT b.id, b.title, b.stock
FROM book b
WHERE b.stock < 30
ORDER BY b.stock ASC;

-- [Q03] 최근 주문 5건 조회
SELECT o.id, o.member_id, o.ordered_at, o.status, o.total_amount
FROM orders o
ORDER BY o.ordered_at DESC
LIMIT 5;

-- [Q04] 완료된 주문 중 결제금액 20,000원 이상인 주문
SELECT o.id, o.member_id, o.ordered_at, o.total_amount
FROM orders o
WHERE o.status = 'completed' AND o.total_amount >= 20000
ORDER BY o.total_amount DESC;

-- ── 조인 Q05~Q08 ─────────────────────────────────────────────────

-- [Q05] 도서와 저자, 장르 이름을 함께 조회 (INNER JOIN)
SELECT b.id, b.title, a.name AS author, g.name AS genre, b.price
FROM book b
INNER JOIN author a ON b.author_id = a.id
INNER JOIN genre  g ON b.genre_id  = g.id
ORDER BY b.price DESC;

-- [Q06] 주문 내역과 회원 이름을 함께 조회 (INNER JOIN)
SELECT o.id AS order_id, m.name AS member,
       o.ordered_at, o.status, o.total_amount
FROM orders o
INNER JOIN member m ON o.member_id = m.id
ORDER BY o.ordered_at DESC;

-- [Q07] 한 번도 주문한 적 없는 회원 목록 (LEFT JOIN)
SELECT m.id, m.name, m.email, m.joined_at
FROM member m
LEFT JOIN orders o ON m.id = o.member_id
WHERE o.id IS NULL;

-- [Q08] 주문 상세 - 도서 제목, 수량, 회원 이름 포함 (3테이블 INNER JOIN)
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
ORDER BY o.id, b.title;

-- ── 집계 Q09~Q11 ─────────────────────────────────────────────────

-- [Q09] 회원별 완료 주문 건수와 총 결제금액 집계 (COUNT + SUM + GROUP BY)
SELECT m.name AS member,
       COUNT(o.id)         AS order_count,
       SUM(o.total_amount) AS total_spent
FROM member m
INNER JOIN orders o ON m.id = o.member_id
WHERE o.status = 'completed'
GROUP BY m.id, m.name
ORDER BY total_spent DESC;

-- [Q10] 저자별 출판 도서 수와 평균 가격 (COUNT + AVG + GROUP BY)
SELECT a.name AS author,
       COUNT(b.id)       AS book_count,
       ROUND(AVG(b.price)) AS avg_price
FROM author a
INNER JOIN book b ON a.id = b.author_id
GROUP BY a.id, a.name
ORDER BY book_count DESC, avg_price DESC;

-- [Q11] 장르별 도서 수와 총 재고 현황 (COUNT + SUM + GROUP BY)
SELECT g.name AS genre,
       COUNT(b.id)    AS book_count,
       SUM(b.stock)   AS total_stock
FROM genre g
INNER JOIN book b ON g.id = b.genre_id
GROUP BY g.id, g.name
ORDER BY book_count DESC;

-- ── 서브쿼리 Q12 ──────────────────────────────────────────────────

-- [Q12] 평균 도서 가격보다 비싼 도서 목록 (서브쿼리)
SELECT id, title, price
FROM book
WHERE price > (SELECT AVG(price) FROM book)
ORDER BY price DESC;

-- ── 데이터 수정 및 삭제 Q13~Q14 ─────────────────────────────────

-- [Q13] 재고 30권 미만 도서의 가격을 5% 인하 (UPDATE)
UPDATE book
SET price = ROUND(price * 0.95)
WHERE stock < 30;

-- [Q14] 취소 상태 주문의 주문 상세 항목 삭제 (DELETE)
DELETE FROM order_item
WHERE order_id IN (
    SELECT id FROM orders WHERE status = 'cancelled'
);

-- ── 인덱스 Q15 ────────────────────────────────────────────────────

-- [Q15] orders.ordered_at 컬럼에 인덱스 생성
-- 적용 이유: 날짜 범위 검색(최근 주문 조회, 기간별 집계)이 가장 빈번하므로
--            인덱스를 통해 풀스캔 없이 범위 조회 성능을 개선한다.
CREATE INDEX IF NOT EXISTS idx_orders_ordered_at ON orders(ordered_at);
