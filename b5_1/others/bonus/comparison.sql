-- ================================================================
-- 보너스 1: 같은 요구를 JOIN 방식과 서브쿼리 방식으로 비교
-- 요구: 가장 많이 팔린 도서(판매 수량 합계 1위)를 구매한 회원 목록
-- ================================================================

-- 방법 A: JOIN 방식
-- 판매 수량이 가장 많은 book_id를 인라인 서브쿼리로 구한 뒤 JOIN으로 회원을 연결한다.
SELECT DISTINCT m.id, m.name, m.email
FROM member m
INNER JOIN orders     o  ON m.id     = o.member_id
INNER JOIN order_item oi ON o.id     = oi.order_id
WHERE oi.book_id = (
    SELECT book_id
    FROM order_item
    GROUP BY book_id
    ORDER BY SUM(quantity) DESC
    LIMIT 1
);

-- 방법 B: 서브쿼리 방식
-- WHERE IN + 중첩 서브쿼리로 동일한 결과를 도출한다.
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
);

-- ── 비교 분석 ────────────────────────────────────────────────────
-- JOIN 방식
--   장점: 옵티마이저가 실행 계획을 유연하게 선택할 수 있다.
--         대용량에서 Hash Join / Merge Join 전략을 활용하기 쉽다.
--   단점: 카디널리티가 높을 때 DISTINCT 처리 비용이 발생할 수 있다.
--
-- 서브쿼리 방식
--   장점: 논리 흐름이 "조건 → 회원"으로 직관적이라 가독성이 좋다.
--   단점: 상관 서브쿼리(correlated)로 변하면 외부 쿼리 행마다 반복 실행된다.
--         (이 예시는 비상관 서브쿼리이므로 실행 횟수는 동일)
--
-- SQLite 3.x에서는 두 쿼리의 EXPLAIN QUERY PLAN 결과가 동일하게 최적화된다.
