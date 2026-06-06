https://801eed90-8fbb-4744-9697-dbae2274bbc5.deploy.dontcode.cafe

  체크리스트 확인

  최소 4개 테이블 + PK 정의

  6개 테이블 전부 INTEGER PRIMARY KEY AUTOINCREMENT 보유:

  ┌────────────┬─────┬─────────────────────────┐
  │   테이블   │ PK  │          역할           │
  ├────────────┼─────┼─────────────────────────┤
  │ genre      │ id  │ 장르 분류               │
  ├────────────┼─────┼─────────────────────────┤
  │ author     │ id  │ 저자 정보               │
  ├────────────┼─────┼─────────────────────────┤
  │ book       │ id  │ 도서 목록               │
  ├────────────┼─────┼─────────────────────────┤
  │ member     │ id  │ 회원 정보               │
  ├────────────┼─────┼─────────────────────────┤
  │ orders     │ id  │ 주문 헤더               │
  ├────────────┼─────┼─────────────────────────┤
  │ order_item │ id  │ 주문 상세 (도서별 수량) │
  └────────────┴─────┴─────────────────────────┘

  FK 1:N 관계 2개 이상 + 없는 값 참조 차단

  5개 FK 관계 존재:
  book.author_id     → author.id
  book.genre_id      → genre.id
  orders.member_id   → member.id
  order_item.order_id → orders.id
  order_item.book_id  → book.id

  없는 값 참조 차단: PRAGMA foreign_keys = ON 상태에서 book_id=999로 INSERT 시도 → FOREIGN KEY constraint failed 확인 (results/bonus/BONUS_FK_result.txt)

  각 테이블 최소 10행

  ┌────────────┬───────┐
  │   테이블   │ 행 수 │
  ├────────────┼───────┤
  │ genre      │ 10    │
  ├────────────┼───────┤
  │ author     │ 10    │
  ├────────────┼───────┤
  │ book       │ 15    │
  ├────────────┼───────┤
  │ member     │ 12    │
  ├────────────┼───────┤
  │ orders     │ 20    │
  ├────────────┼───────┤
  │ order_item │ 28    │
  └────────────┴───────┘

  쿼리 15개

  ┌───────────────┬─────────┬─────────────────────────────────────────────┐
  │     범주      │  번호   │                   핵심 절                   │
  ├───────────────┼─────────┼─────────────────────────────────────────────┤
  │ 기본 조회 4개 │ Q01~Q04 │ ORDER BY / WHERE / LIMIT / AND 조합         │
  ├───────────────┼─────────┼─────────────────────────────────────────────┤
  │ 조인 4개      │ Q05~Q08 │ INNER JOIN ×2, INNER JOIN ×3, LEFT JOIN     │
  ├───────────────┼─────────┼─────────────────────────────────────────────┤
  │ 집계 3개      │ Q09~Q11 │ COUNT+SUM, COUNT+AVG, COUNT+SUM             │
  ├───────────────┼─────────┼─────────────────────────────────────────────┤
  │ 서브쿼리 1개  │ Q12     │ WHERE price > (SELECT AVG(price) FROM book) │
  ├───────────────┼─────────┼─────────────────────────────────────────────┤
  │ 수정/삭제 2개 │ Q13~Q14 │ UPDATE, DELETE                              │
  ├───────────────┼─────────┼─────────────────────────────────────────────┤
  │ 인덱스 1개    │ Q15     │ CREATE INDEX                                │
  └───────────────┴─────────┴─────────────────────────────────────────────┘

  실행 결과 첨부: results/Q01_result.txt ~ Q15_result.txt + results/bonus/ 22개 파일 모두 커밋에 포함.

  ---
  구술 평가 예상 질문

  테이블을 왜 이렇게 나눴는가?

  "책 한 권"을 엑셀처럼 한 줄에 기록하면 저자명, 장르명이 도서마다 반복된다. 저자를 200권 출판했으면 저자 국적이 200번 중복 저장되고, 국적이 바뀌면 200행을 전부 수정해야
  한다. 테이블을 나누면 author 테이블에 1행만 있고 book은 author_id로 참조한다. 수정은 1곳, 저장공간 절약, 실수 가능성 제거가 핵심이다.

  order_item을 분리한 이유: 주문 한 건에 여러 도서가 담길 수 있다. orders에 "book1, book2, book3"을 컬럼 하나에 쉼표로 넣으면 쿼리가 불가능해진다. order_item으로 분리하면
  SELECT * FROM order_item WHERE order_id = 1으로 바로 조회된다.

  FK 1:N 관계가 실제 도메인에서 어떤 의미인가?

  member(1) ↔ orders(N): 회원 한 명이 여러 번 주문할 수 있다. 이서연(id=2)의 orders를 보면 주문 2번, 8번, 20번 세 건이 모두 member_id=2를 가리킨다. FK가 없으면
  member_id=999처럼 존재하지 않는 회원 주문이 쌓일 수 있다.

  orders(1) ↔ order_item(N): 주문 7번(강하은)에는 "죄와 벌 1권 + 어린왕자 2권" 두 줄이 order_id=7로 연결된다. 헤더(총금액, 일시, 상태)는 orders에 1번만 저장하고 상세는
  order_item에 여러 행으로 분리한다.

  컬럼 타입을 왜 그렇게 선택했는가?

  - price, stock, quantity, total_amount: INTEGER. 금액을 REAL(부동소수점)로 저장하면 0.1+0.2 = 0.30000000000000004 같은 부동소수점 오차가 발생한다. 원화는 소수점이
  없으므로 INTEGER가 정확하다.
  - email, isbn, title, name: TEXT. SQLite의 TEXT는 가변길이이므로 VARCHAR(255) 같은 크기 제한 없이 유연하게 저장된다.
  - ordered_at, published_date, joined_at: SQLite에는 DATETIME 타입이 없다. TEXT로 'YYYY-MM-DD HH:MM:SS' 형식을 저장하면 문자열 정렬이 곧 시간순 정렬이 되어 ORDER BY
  ordered_at DESC가 정상 동작한다.
  - status: TEXT + CHECK(status IN ('pending','completed','cancelled')). ENUM이 없는 SQLite에서 CHECK로 허용값을 제한해 잘못된 상태값 입력을 막는다.

  인덱스를 어느 컬럼에 걸었고 왜 그 컬럼인가?

  CREATE INDEX idx_orders_ordered_at ON orders(ordered_at).

  선택 이유 3가지:
  1. Q03에서 ORDER BY ordered_at DESC LIMIT 5처럼 정렬 기준으로 매우 자주 쓰인다.
  2. 실무에서 "최근 30일 주문", "월별 집계" 같은 날짜 범위 검색이 가장 빈번한 패턴이다.
  3. member_id는 회원별 주문이 평균 1.7건으로 적어 인덱스 효과가 낮지만, ordered_at은 모든 주문이 다른 값을 가져 선택도(selectivity)가 높다.

  인덱스를 걸지 않으면 20만 건의 주문 테이블에서 ORDER BY ordered_at는 풀스캔 후 정렬이 필요하다. 인덱스가 있으면 B-tree 순회로 바로 앞/뒤 값을 찾는다.

  ---
  개념 설명

  데이터베이스와 엑셀의 차이

  엑셀의 한계: 한 셀에 "한강 / 소설 / 채식주의자 / 13500" 을 한 행에 담으면 "한강이 쓴 모든 책의 총 재고"를 수식 하나로 구하기 어렵다. 저자 이름이 오타나면 찾아서 고쳐야
  하는 행 수를 모른다. 두 사람이 동시에 같은 셀을 수정하면 데이터가 덮어씌워진다.

  DB의 차이: 관계를 테이블로 표현한다. author.id를 book.author_id가 참조하므로 저자 이름 수정은 1행만 바꾸면 된다. FK가 없는 값 참조를 막으므로 고아 데이터가 생기지
  않는다. 트랜잭션으로 동시 수정 충돌을 제어한다.

  PK와 FK 역할 구분

  - PK(author.id): 그 행의 고유 식별자. 절대 중복되지 않고 NULL이 될 수 없다. "이 저자를 가리키는 주소"다.
  - FK(book.author_id): 다른 테이블의 PK를 참조하는 포인터. book.author_id = 3이면 author 테이블의 id=3("무라카미 하루키")을 가리킨다.

  본 스키마에서: book 15행 중 author_id=1인 것이 3행(채식주의자, 소년이 온다, 흰) — 이게 1:N의 실제 모습이다.

  INNER JOIN vs LEFT JOIN 차이

  Q05(INNER JOIN): book INNER JOIN author → 저자가 있는 도서만 15행 반환. author가 없는 book은 결과에서 제외된다.

  Q07(LEFT JOIN): member LEFT JOIN orders → 주문이 0건인 회원도 결과에 포함된다. WHERE o.id IS NULL로 주문이 없는 회원만 필터링. 현재 샘플 데이터에서는 12명 모두 최소
  1건의 주문이 있어 "결과 없음"이 나온다 — 이는 LEFT JOIN 로직이 올바르게 동작한다는 증거이며 데이터가 완전하다는 의미다. (회원 한 명을 삭제하면 즉시 해당 회원이 결과에
  나타난다.)

  GROUP BY와 집계 함수 동작 방식

  Q09 결과를 기준으로: GROUP BY m.id, m.name은 같은 회원의 주문 행들을 하나로 묶는다. 이서연(id=2)의 주문은 2번(20,000), 8번(13,000), 20번(34,500) 세 행 → COUNT = 3, SUM =
  67,500. 묶기 전 3행이 묶인 후 1행이 되는 것이 GROUP BY의 핵심이다.

  가장 복잡했던 쿼리 단계별 설명

  Q08 (3테이블 INNER JOIN):
  SELECT o.id, m.name, b.title, oi.quantity, oi.unit_price,
         (oi.quantity * oi.unit_price) AS subtotal
  FROM order_item oi
  INNER JOIN orders o ON oi.order_id = o.id   -- 1단계: 상세에 주문 정보 붙이기
  INNER JOIN member m ON o.member_id = m.id   -- 2단계: 주문에 회원 이름 붙이기
  INNER JOIN book   b ON oi.book_id  = b.id   -- 3단계: 상세에 도서 제목 붙이기
  ORDER BY o.id, b.title

  풀이 순서: ① order_item이 중심 테이블 — 여기서 시작하는 이유는 "수량과 단가"가 여기 있기 때문. ② orders를 JOIN해 주문일시·상태 획득. ③ member를 JOIN해 회원 이름 획득. ④
  book을 JOIN해 도서 제목 획득. ⑤ subtotal = quantity × unit_price는 저장된 컬럼이 아니라 SELECT 시점에 계산.

  가장 어려웠던 부분

  order_item의 unit_price를 도서 현재 가격이 아닌 "주문 시점 가격"으로 설계한 것. book.price에 직접 참조하면 Q13(가격 5% 인하 UPDATE) 실행 후 과거 주문 금액이
  바뀌어버린다. order_item에 unit_price를 독립 컬럼으로 두어 주문 시점 가격을 스냅샷으로 저장했다 — 실무 이커머스 설계와 동일한 패턴이다.
