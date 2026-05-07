-- ── users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       VARCHAR(36)  PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    username      VARCHAR(120) NOT NULL DEFAULT 'reader',
    password_hash VARCHAR(255) NULL,
    google_id     VARCHAR(255) NULL,
    theme         VARCHAR(10)  NOT NULL DEFAULT 'system',
    created_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_users_google (google_id)
);

-- ── genres ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS genres (
    genre_id  INT          AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL UNIQUE
);

-- ── authors ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS authors (
    author_id  VARCHAR(36)  PRIMARY KEY,
    user_id    VARCHAR(36)  NOT NULL,
    name       VARCHAR(255) NOT NULL,
    country    VARCHAR(100) NOT NULL DEFAULT '',
    dob        VARCHAR(10)  NOT NULL DEFAULT '',
    awards     JSON         NOT NULL,
    CONSTRAINT fk_authors_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_authors_user_name (user_id, name)
);

-- ── books ─────────────────────────────────────────────────────────────────────
-- status ∈ {available, lent, reading, read, sold}
CREATE TABLE IF NOT EXISTS books (
    isbn         VARCHAR(20)   NOT NULL,
    user_id      VARCHAR(36)   NOT NULL,
    title        VARCHAR(255)  NOT NULL,
    author_id    VARCHAR(36)   NOT NULL,
    pages        INT           NOT NULL DEFAULT 0,
    year         INT           NOT NULL DEFAULT 0,
    publisher    VARCHAR(255)  NOT NULL DEFAULT '',
    status       VARCHAR(20)   NOT NULL DEFAULT 'available',
    format       VARCHAR(20)   NOT NULL DEFAULT 'paperback',
    description  TEXT          NULL,
    rating       TINYINT       NULL,
    thoughts     TEXT          NULL,
    date_added   VARCHAR(10)   NOT NULL,
    date_read    VARCHAR(10)   NULL,
    sale_price   DECIMAL(10,2) NULL,
    sale_date    VARCHAR(10)   NULL,
    cover_url    VARCHAR(500)  NULL,
    borrower     VARCHAR(120)  NULL,
    due_date     VARCHAR(10)   NULL,
    PRIMARY KEY (isbn, user_id),
    CONSTRAINT fk_books_author FOREIGN KEY (author_id) REFERENCES authors(author_id),
    CONSTRAINT fk_books_user   FOREIGN KEY (user_id)   REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_books_user_status    (user_id, status),
    INDEX idx_books_user_year      (user_id, year),
    INDEX idx_books_user_date_added(user_id, date_added),
    INDEX idx_books_user_date_read (user_id, date_read)
);

-- ── book_genres ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS book_genres (
    isbn      VARCHAR(20) NOT NULL,
    user_id   VARCHAR(36) NOT NULL,
    genre_id  INT         NOT NULL,
    PRIMARY KEY (isbn, user_id, genre_id),
    CONSTRAINT fk_bg_book  FOREIGN KEY (isbn, user_id) REFERENCES books(isbn, user_id) ON DELETE CASCADE,
    CONSTRAINT fk_bg_genre FOREIGN KEY (genre_id)      REFERENCES genres(genre_id)     ON DELETE CASCADE
);

-- ── wishlist ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wishlist (
    isbn         VARCHAR(20)  NOT NULL,
    user_id      VARCHAR(36)  NOT NULL,
    title        VARCHAR(255) NOT NULL,
    author_name  VARCHAR(255) NOT NULL DEFAULT '',
    year         INT          NOT NULL DEFAULT 0,
    cover_url    VARCHAR(500) NULL,
    buy_url      VARCHAR(500) NULL,
    PRIMARY KEY (isbn, user_id),
    CONSTRAINT fk_wishlist_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ── wishlist_genres ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wishlist_genres (
    isbn      VARCHAR(20) NOT NULL,
    user_id   VARCHAR(36) NOT NULL,
    genre_id  INT         NOT NULL,
    PRIMARY KEY (isbn, user_id, genre_id),
    CONSTRAINT fk_wg_wishlist FOREIGN KEY (isbn, user_id) REFERENCES wishlist(isbn, user_id) ON DELETE CASCADE,
    CONSTRAINT fk_wg_genre    FOREIGN KEY (genre_id)      REFERENCES genres(genre_id)        ON DELETE CASCADE
);

-- ── activity ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity (
    id         BIGINT      AUTO_INCREMENT PRIMARY KEY,
    user_id    VARCHAR(36) NOT NULL,
    action     VARCHAR(40) NOT NULL,
    isbn       VARCHAR(20) NULL,
    detail     VARCHAR(255) NOT NULL DEFAULT '',
    timestamp  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_activity_user_ts (user_id, timestamp)
);
