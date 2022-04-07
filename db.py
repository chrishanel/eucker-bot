import os
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Game(Base):
    """
    Available games to be wagered upon, and other metadata
    """

    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(128))
    away_team = db.Column(db.String(128))
    date = db.Column(db.Date)
    season = db.Column(db.Integer)
    week = db.Column(db.Integer)
    dh = db.Column(db.Integer)
    date_changed = db.Column(db.Boolean)
    outcomes = relationship("Outcome", back_populates="game")


class Outcome(Base):
    """
    A list of `outcome` which are `wagered` on. This will be filled by the schedules API (or some other mechanism)
    """

    __tablename__ = "outcomes"
    id = db.Column(db.String, primary_key=True)
    selection_name = db.Column(db.String)
    outcome_date = db.Column(db.Date)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    result = db.Column(db.Integer)
    runs = db.Column(db.Integer)


class Wager(Base):
    """
    A given `user` makes a `wager`... this is then checked against the outcome to determine results
    """

    __tablename__ = "wagers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    wager_amount = db.Column(db.Integer)
    outcome_id = db.Column(db.Integer, db.ForeignKey("outcomes.id"))


class User(Base):
    """
    Base table for a given individual, mapping to their discord user id
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(255))

    balance = relationship("Balance", uselist=False, backref="user")


class Balance(Base):
    """
    A table which tracks the current balance of a given user
    """

    __tablename__ = "balances"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    balance_amount = db.Column(db.BigInteger)


class Bonus(Base):
    """
    A list of the universe of bonuses available for users to have
    """

    __tablename__ = "bonuses"

    id = db.Column(db.Integer, primary_key=True)
    bonus_name = db.Column(db.String(255))


class UserBonus(Base):
    """
    The bonuses applied to a given user and when that bonus will be applied
    """

    __tablename__ = "users_bonuses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    bonus_id = db.Column(db.Integer, db.ForeignKey("bonuses.id"))
    status = db.Column(db.Integer)
    efft_d = db.Column(db.DateTime)
    expy_d = db.Column(db.DateTime)


def main():
    DB_CONN_URI = os.environ.get("DB_CONN_URI", "sqlite:///main.db")
    engine = db.create_engine(DB_CONN_URI)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
