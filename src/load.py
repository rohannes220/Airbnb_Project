
import csv
import gzip
import sqlite3
from pathlib import Path

DB_PATH = Path("data/derived/airbnb.db")
DATA_PATH = Path("data/raw/build")


def read_csv(filename):
    with gzip.open(DATA_PATH / filename, "rt", encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)


def parse_price(value):
    if not value or value.strip() in ("", "NA", "N/A"):
        return None
    return float(value.replace("$", "").replace(",", ""))


def parse_number(value, number_type):
    if value is None or value.strip() == "":
        return None
    return number_type(value)


def load_data():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    counts = {"hosts": 0, "listings": 0, "reviews": 0}
    rejected = {"listings": 0, "reviews": 0}

    for table in ("reviews", "listings", "hosts"):
        connection.execute(f"DELETE FROM {table}")

    for row in read_csv("listings.csv.gz"):
        try:
            host_id = int(row["host_id"])
            listing_id = int(row["id"])

            listing_values = (
                listing_id,
                host_id,
                row["name"],
                row["neighbourhood_cleansed"],
                row["room_type"],
                parse_price(row["price"]),
                parse_number(row["accommodates"], int),
                parse_number(row["review_scores_rating"], float),
                parse_number(row["number_of_reviews"], int),
            )

            connection.execute("SAVEPOINT listing_row")

            connection.execute(
                """INSERT OR IGNORE INTO hosts
                (host_id, host_name, host_since, host_location,
                 host_is_superhost, host_identity_verified)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    host_id,
                    row["host_name"],
                    row["host_since"],
                    row["host_location"],
                    row["host_is_superhost"],
                    row["host_identity_verified"],
                ),
            )

            connection.execute(
                """INSERT INTO listings
                (id, host_id, name, neighbourhood_cleansed, room_type,
                 price, accommodates, review_scores_rating, number_of_reviews)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                listing_values,
            )

            connection.execute("RELEASE SAVEPOINT listing_row")
            counts["listings"] += 1

        except (ValueError, TypeError, sqlite3.IntegrityError) as error:
            connection.execute("ROLLBACK TO SAVEPOINT listing_row") if connection.in_transaction else None
            connection.execute("RELEASE SAVEPOINT listing_row") if connection.in_transaction else None
            rejected["listings"] += 1
            print(f"Rejected listing {row.get('id')}: {error}")

    counts["hosts"] = connection.execute(
        "SELECT COUNT(*) FROM hosts"
    ).fetchone()[0]

    for row in read_csv("reviews.csv.gz"):
        try:
            connection.execute(
                """INSERT INTO reviews
                (id, listing_id, date, reviewer_id, reviewer_name, comments)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    int(row["id"]),
                    int(row["listing_id"]),
                    row["date"],
                    parse_number(row["reviewer_id"], int),
                    row["reviewer_name"],
                    row["comments"],
                ),
            )
            counts["reviews"] += 1

        except (ValueError, TypeError, sqlite3.IntegrityError) as error:
            rejected["reviews"] += 1

    connection.commit()
    connection.close()

    print("\nData loading complete!")
    print("Inserted:", counts)
    print("Rejected:", rejected)


if __name__ == "__main__":
    load_data()
