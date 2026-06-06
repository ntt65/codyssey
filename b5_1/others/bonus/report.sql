-- ================================================================
-- 보너스 3: 미니 리포트 - 핵심 지표 3개
-- ================================================================

-- 지표 1: 월별 주문 건수 및 총 매출 추이 (completed 주문 기준)
-- 어느 달에 매출이 집중되는지 파악하는 지표
SELECT strftime('%Y-%m', ordered_at) AS month,
       COUNT(id)                      AS order_count,
       SUM(total_amount)              AS monthly_revenue
FROM orders
WHERE status = 'completed'
GROUP BY month
ORDER BY month;

-- 지표 2: 가장 많이 팔린 도서 TOP 5 (판매 수량 합계 기준)
-- 재고 보충 우선순위 및 인기 도서 파악에 활용
SELECT b.title,
       a.name                          AS author,
       SUM(oi.quantity)                AS total_sold,
       SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM order_item oi
INNER JOIN book   b ON oi.book_id  = b.id
INNER JOIN author a ON b.author_id = a.id
GROUP BY b.id, b.title, a.name
ORDER BY total_sold DESC
LIMIT 5;

-- 지표 3: 구매 금액 기준 상위 회원 TOP 3 (VIP 고객 선별)
-- 마케팅/멤버십 혜택 대상 선정에 활용
SELECT m.name,
       m.email,
       COUNT(o.id)         AS order_count,
       SUM(o.total_amount) AS lifetime_value
FROM member m
INNER JOIN orders o ON m.id = o.member_id
WHERE o.status = 'completed'
GROUP BY m.id, m.name, m.email
ORDER BY lifetime_value DESC
LIMIT 3;
