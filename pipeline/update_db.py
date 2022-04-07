import os
from datetime import date
from argparse import ArgumentParser

import sqlalchemy
import pandas as pd


DB_CONN_URI = os.environ.get("DB_CONN_URI", "sqlite:///main.db")
GAMES_TABLE = os.environ.get("GAMES_TABLE", "games")
OUTCOMES_TABLE = os.environ.get("OUTCOMES_TABLE", "outcomes")
DATA_DIR = os.environ.get("UECKER_DATA_DIR", "output")

GAME_COLS = [
    "id",
    "home_team",
    "away_team",
    "date",
    "season",
    "week",
    "dh",
    "date_changed",
]
OUTCOME_COLS = ["id", "selection_name", "outcome_date", "game_id", "result", "runs"]


def load_data(date_str):
    games = pd.read_csv(os.path.join(DATA_DIR, f"schedule_{date_str}.csv"))
    outcomes = pd.read_csv(os.path.join(DATA_DIR, f"outcomes_{date_str}.csv"))
    return games, outcomes


def get_db_connection():
    eng = sqlalchemy.create_engine(DB_CONN_URI)
    return eng


def update_games(data, eng):
    with eng.begin() as conn:
        for _, row in data.iterrows():
            stmt = f"SELECT * FROM {GAMES_TABLE} WHERE id = {row['id']};"
            game = conn.execute(stmt).first()
            # if game not in DB, insert all values and move on
            if not game:
                values = tuple(row[GAME_COLS])
                stmt = f"INSERT INTO {GAMES_TABLE} VALUES {values};"
                conn.execute(stmt)
                continue
            # if postponed/suspended, flag as date changed and nullify date
            if row["date_changed"]:
                stmt = (
                    f"UPDATE {GAMES_TABLE} "
                    f"SET date_changed = True, date = null "
                    f"WHERE id = {row['id']};"
                )
                conn.execute(stmt)
            # for games already in DB, update date/week/doubleheader
            dt, wk, dh = row["date"], row["week"], row["dh"]
            stmt = (
                f"UPDATE {GAMES_TABLE} "
                f"SET date = '{dt}', week = {wk}, dh = {dh} "
                f"WHERE id = {row['id']};"
            )
            conn.execute(stmt)


def update_outcomes(data, eng):
    with eng.begin() as conn:
        for _, row in data.iterrows():
            stmt = f"SELECT * FROM {OUTCOMES_TABLE} WHERE id = '{row['id']}';"
            oc = conn.execute(stmt).first()
            # if outcome not in DB, insert all values and move on
            if not oc:
                values = tuple(row[OUTCOME_COLS])
                stmt = f"INSERT INTO {OUTCOMES_TABLE} VALUES {values};"
                conn.execute(stmt)
                continue
            # for outcomes already in DB, update result, date, and runs
            res, ocd, runs = row["result"], row["outcome_date"], row["runs"]
            stmt = (
                f"UPDATE {OUTCOMES_TABLE} "
                f"SET result = {res}, outcome_date = '{ocd}', runs = {runs} "
                f"WHERE id = '{row['id']}';"
            )
            conn.execute(stmt)


def main(date_str=None):
    eng = get_db_connection()
    if date_str is None:
        date_str = date.today().isoformat()
    games, outcomes = load_data(date_str)
    update_games(games, eng)
    update_outcomes(outcomes, eng)


if __name__ == "__main__":
    parser = ArgumentParser(description="Ingest scraped data into uecker-bot database.")
    parser.add_argument(
        "--date",
        help="Date of data files in YYYY-MM-DD format",
        default=None,
        required=False,
    )
    args = parser.parse_args()
    main(args.date)
