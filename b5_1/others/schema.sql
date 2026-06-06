PRAGMA foreign_keys = ON;

-- ================================================================
-- 온라인 서점 (Online Bookstore) - 스키마 정의
-- DB: SQLite
-- 테이블: genre, author, book, member, orders, order_item
--
-- 1:N 관계
--   genre  → book        (장르 1 : 도서 N)
--   author → book        (저자 1 : 도서 N)
--   member → orders      (회원 1 : 주문 N)
--   orders → order_item  (주문 1 : 주문상세 N)
--   book   → order_item  (도서 1 : 주문상세 N)
-- ================================================================

-- ── 장르 테이블 ─────────────────────────────────────────────────
CREATE TABLE genre (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,       -- UNIQUE: 장르명 중복 불가
    description TEXT
);

-- ── 저자 테이블 ─────────────────────────────────────────────────
CREATE TABLE author (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    nationality TEXT    NOT NULL,
    birth_year  INTEGER
);

-- ── 도서 테이블 ─────────────────────────────────────────────────
CREATE TABLE book (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_id       INTEGER NOT NULL,
    author_id      INTEGER NOT NULL,
    title          TEXT    NOT NULL,
    isbn           TEXT    NOT NULL UNIQUE,    -- UNIQUE: ISBN 중복 불가
    price          INTEGER NOT NULL CHECK (price > 0),
    stock          INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    published_date TEXT,
    FOREIGN KEY (genre_id)  REFERENCES genre(id),
    FOREIGN KEY (author_id) REFERENCES author(id)
);

-- ── 회원 테이블 ─────────────────────────────────────────────────
CREATE TABLE member (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    email     TEXT NOT NULL UNIQUE,            -- UNIQUE: 이메일 중복 불가
    phone     TEXT,
    joined_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ── 주문 테이블 ─────────────────────────────────────────────────
CREATE TABLE orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id    INTEGER NOT NULL,
    ordered_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    status       TEXT    NOT NULL DEFAULT 'completed'
                          CHECK (status IN ('pending', 'completed', 'cancelled')),
    total_amount INTEGER NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    FOREIGN KEY (member_id) REFERENCES member(id)
);

-- ── 주문 상세 테이블 ────────────────────────────────────────────
CREATE TABLE order_item (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL,
    book_id    INTEGER NOT NULL,
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (book_id)  REFERENCES book(id)
);
