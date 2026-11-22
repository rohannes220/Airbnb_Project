PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS hosts (
    host_id INTEGER PRIMARY KEY,
    host_name TEXT,
    host_since TEXT,
    host_location TEXT,
    host_is_superhost TEXT,
    host_identity_verified TEXT
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY,
    host_id INTEGER NOT NULL,
    name TEXT,
    neighbourhood_cleansed TEXT,
    room_type TEXT,
    price REAL CHECK (price IS NULL OR price >= 0),
    accommodates INTEGER CHECK (
        accommodates IS NULL OR accommodates >= 0
    ),
    review_scores_rating REAL CHECK (
        review_scores_rating IS NULL
        OR review_scores_rating BETWEEN 0 AND 5
    ),
    number_of_reviews INTEGER CHECK (
        number_of_reviews IS NULL OR number_of_reviews >= 0
    ),
    FOREIGN KEY (host_id) REFERENCES hosts(host_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    listing_id INTEGER NOT NULL,
    date TEXT,
    reviewer_id INTEGER,
    reviewer_name TEXT,
    comments TEXT,
    FOREIGN KEY (listing_id) REFERENCES listings(id)
);
