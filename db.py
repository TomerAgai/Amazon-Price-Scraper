import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def initialize_db(conn):
    try:
        cursor = conn.cursor()
        create_table_sql = """CREATE TABLE IF NOT EXISTS searches (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                asin TEXT NOT NULL,
                                name TEXT NOT NULL,
                                image TEXT NOT NULL,
                                price TEXT NOT NULL,
                                link TEXT NOT NULL,
                                rating REAL,
                                timestamp TEXT NOT NULL
                            );"""

        cursor.execute(create_table_sql)
        conn.commit()
    except Error as e:
        print(e)


def insert_search_result(conn, search_result):
    try:
        cursor = conn.cursor()
        insert_sql = """INSERT INTO searches(asin, name, image, price, link, rating, timestamp)
                        VALUES(?, ?, ?, ?, ?, ?, ?)"""

        cursor.execute(insert_sql, (search_result["asin"], search_result["name"],
                       search_result["image"], search_result["price"], search_result["link"], search_result["rating"], search_result["timestamp"]))
        print(search_result)
        conn.commit()
    except Error as e:
        print(e)


def get_past_searches(conn):
    try:
        cursor = conn.cursor()
        select_sql = "SELECT * FROM searches"

        cursor.execute(select_sql)
        rows = cursor.fetchall()

        return rows
    except Error as e:
        print(e)

    return []


def count_searches_today(conn, search_date):
    try:
        cursor = conn.cursor()
        select_sql = """SELECT COUNT(*) FROM searches 
                        WHERE strftime('%Y-%m-%d', timestamp) = ?"""

        cursor.execute(select_sql, (search_date,))
        count = cursor.fetchone()[0] / 10

        return count
    except Error as e:
        print(e)

    return 0


# def print_all_searches(database_file):
#     try:
#         conn = sqlite3.connect(database_file)
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM searches")
#         rows = cursor.fetchall()
#         print("All rows in the searches table:")
#         for row in rows:
#             print(row)
#         conn.close()
#     except sqlite3.Error as e:
#         print(e)
