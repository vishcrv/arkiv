CREATE TABLE IF NOT EXISTS authors (
    author_id   VARCHAR(16)  PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    country     VARCHAR(100) NOT NULL DEFAULT '',
    dob         VARCHAR(10)  NOT NULL DEFAULT '',
    awards      JSON         NOT NULL,
    INDEX idx_authors_name (name)
);

CREATE TABLE IF NOT EXISTS books (
    isbn         VARCHAR(20)  PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    author_id    VARCHAR(16)  NOT NULL,
    pages        INT          NOT NULL DEFAULT 0,
    year         INT          NOT NULL DEFAULT 0,
    genre        VARCHAR(100) NOT NULL DEFAULT '',
    publisher    VARCHAR(255) NOT NULL DEFAULT '',
    status       VARCHAR(20)  NOT NULL DEFAULT 'available',
    format       VARCHAR(20)  NOT NULL DEFAULT 'paperback',
    description  TEXT         NULL,
    rating       TINYINT      NULL,
    thoughts     TEXT         NULL,
    date_added   VARCHAR(10)  NOT NULL,
    date_read    VARCHAR(10)  NULL,
    sale_price   DECIMAL(10,2) NULL,
    sale_date    VARCHAR(10)  NULL,
    cover_url    VARCHAR(500) NULL,
    borrower     VARCHAR(120) NULL,
    due_date     VARCHAR(10)  NULL,
    CONSTRAINT fk_books_author FOREIGN KEY (author_id) REFERENCES authors(author_id),
    INDEX idx_books_status (status),
    INDEX idx_books_year (year),
    INDEX idx_books_genre (genre),
    INDEX idx_books_date_read (date_read)
);

CREATE TABLE IF NOT EXISTS wishlist (
    isbn         VARCHAR(20)  PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    author_name  VARCHAR(255) NOT NULL DEFAULT '',
    year         INT          NOT NULL DEFAULT 0,
    genre        VARCHAR(100) NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS activity (
    id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
    action     VARCHAR(40)  NOT NULL,
    isbn       VARCHAR(20)  NULL,
    detail     VARCHAR(255) NOT NULL DEFAULT '',
    timestamp  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_activity_timestamp (timestamp)
);

CREATE TABLE IF NOT EXISTS profile (
    id          TINYINT      PRIMARY KEY DEFAULT 1,
    username    VARCHAR(120) NOT NULL DEFAULT 'reader',
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHECK (id = 1)
);
INSERT IGNORE INTO profile (id, username) VALUES (1, 'reader');