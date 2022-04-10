import os
import sys
from datetime import date
from argparse import ArgumentParser

import sqlalchemy
import pandas as pd


# expose modules in parent directory
sys.path.append(os.path.abspath(".."))

from db import Game, Outcome, Session


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
    games.date = pd.to_datetime(games.date).dt.date
    outcomes = pd.read_csv(os.path.join(DATA_DIR, f"outcomes_{date_str}.csv"))
    outcomes.outcome_date = pd.to_datetime(outcomes.outcome_date).dt.date
    return games, outcomes


def update_games(data, session):
    for _, row in data.iterrows():
        game = session.query(Game).filter(Game.id == row["id"]).first()
        # if game not in DB, create new row
        if not game:
            game = Game(**row)
        # if postponed/suspended, flag as date changed and nullify date
        if row["date_changed"]:
            game.date_changed = True
            game.date = None
        # otherwise ensure date/week/dh are correct
        else:
            if game.date != row["date"]:
                game.date = row["date"]
                game.week = row["week"]
            if game.dh != row.dh:
                game.dh = row["dh"]
        session.add(game)


def update_outcomes(data, session):
    for _, row in data.iterrows():
        oc = session.query(Outcome).filter(Outcome.id == row["id"]).first()
        # if outcome not in DB, create new row
        if not oc:
            oc = Outcome(**row)
        # if game is complete, update row with results
        if oc.result != row["result"]:
            oc.result = row["result"]
            oc.outcome_date = row["outcome_date"]
            oc.runs = row["runs"]
        session.add(oc)


def main(date_str=None):
    if date_str is None:
        date_str = date.today().isoformat()
    games, outcomes = load_data(date_str)
    with Session.begin() as session:
        update_games(games, session)
        update_outcomes(outcomes, session)


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
