SET FOREIGN_KEY_CHECKS = 0;

-- AUTHORS
LOAD DATA LOCAL INFILE 'C:/Users/PC/dev/projs/arkiv/migration/mysql_ready/authors.csv'
INTO TABLE authors
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(author_id, name, country, dob, awards);

-- BOOKS
LOAD DATA LOCAL INFILE 'C:/Users/PC/dev/projs/arkiv/migration/mysql_ready/books.csv'
INTO TABLE books
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(isbn, title, author_id, pages, year, genre, publisher, status, format,
 @description, @rating, @thoughts, date_added, @date_read,
 @sale_price, @sale_date, @cover_url, @borrower, @due_date)
SET
 description = NULLIF(@description, ''),
 rating      = NULLIF(@rating, ''),
 thoughts    = NULLIF(@thoughts, ''),
 date_read   = NULLIF(@date_read, ''),
 sale_price  = NULLIF(@sale_price, ''),
 sale_date   = NULLIF(@sale_date, ''),
 cover_url   = NULLIF(@cover_url, ''),
 borrower    = NULLIF(@borrower, ''),
 due_date    = NULLIF(@due_date, '');

-- WISHLIST
LOAD DATA LOCAL INFILE 'C:/Users/PC/dev/projs/arkiv/migration/mysql_ready/wishlist.csv'
INTO TABLE wishlist
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(isbn, title, author_name, year, genre);

-- ACTIVITY
LOAD DATA LOCAL INFILE 'C:/Users/PC/dev/projs/arkiv/migration/mysql_ready/activity.csv'
INTO TABLE activity
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(action, @isbn, detail, timestamp)
SET isbn = NULLIF(@isbn, '');

SET FOREIGN_KEY_CHECKS = 1;

-- REPORT
SELECT 'authors'  AS tbl, COUNT(*) AS n FROM authors  UNION ALL
SELECT 'books',   COUNT(*) FROM books   UNION ALL
SELECT 'wishlist',COUNT(*) FROM wishlist UNION ALL
SELECT 'activity',COUNT(*) FROM activity;