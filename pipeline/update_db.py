import os
from datetime import date
from argparse import ArgumentParser

import sqlalchemy
import pandas as pd


DB_CONN_URI = os.environ.get("DB_CONN_URI", "sqlite:///main.db")
GAMES_TABLE = os.environ.get("GAMES_TABLE", "games")
OUTCOMES_TABLE = os.environ.get("OUTCOMES_TABLE", "outcomes")
DATA_DIR = os.environ.get("UECKER_DATA_DIR", ".")


def load_data(date_str):
    games = pd.read_csv(os.path.join(DATA_DIR, f"schedule_{date_str}.csv"))
    outcomes = pd.read_csv(os.path.join(DATA_DIR, f"outcomes_{date_str}.csv"))
    return games, outcomes


def get_db_connection():
    eng = sqlalchemy.create_engine(DB_CONN_URI)
    return eng


def update_table(data, table, eng):
    with eng.begin() as conn:
        # create temporary table with new data
        data.to_sql("tmp", conn, index=False, if_exists="replace")
        # remove those rows from games
        stmt = f"DELETE FROM {table} WHERE id IN (SELECT id FROM tmp);"
        conn.execute(stmt)
        # insert new data into games
        data.to_sql(table, conn, index=False, if_exists="append")
        conn.execute("DROP TABLE tmp;")


def main(date_str=None):
    eng = get_db_connection()
    if date_str is None:
        date_str = date.today().isoformat()
    games, outcomes = load_data(date_str)
    update_table(games, GAMES_TABLE, eng)
    update_table(outcomes, OUTCOMES_TABLE, eng)


if __name__ == "__main__":
    parser = ArgumentParser(description="Ingest scraped data into uecker-bot database.")
    parser.add_argument("--date",
                        help="Date of data files in YYYY-MM-DD format",
                        default=None, required=False)
    args = parser.parse_args()
    main(args.date)
