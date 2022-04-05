import datetime
import os
from typing import List
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
from db import Base, User, Balance, Game, Outcome, Wager


class BattlegroundGame:
    def _setup_db(self, conn_str):
        """Sets up the connection to the database"""
        self.engine = db.create_engine(conn_str)
        self.Session = sessionmaker()
        self.Session.configure(bind=self.engine)
        self.session = self.Session()

    def _close_db(self):
        """Closes the connection to the database"""
        self.session.close()

    def __init__(self, conn_str=None):
        if not conn_str:
            conn_str = os.environ.get("DB_CONN_URI", "sqlite:///main.db")
        self._setup_db(conn_str)

    def get_or_create_user(self, discord_id: str) -> User:
        """Get's an existing user by their discord identifier, creating one
        if none exists
        """
        user = self.session.query(User).filter(User.discord_id == discord_id).first()
        if not user:
            user = User(discord_id=discord_id)
            self.session.add(user)
            balance = Balance(user_id=user.id, balance_amount=0)
            self.session.add(balance)
            self.session.commit()
        return user

    def get_todays_games(self) -> List[Game]:
        """Gets all games for the current day"""
        today = datetime.date.today()
        games = self.session.query(Game).filter(Game.date == today).all()
        return games
    
    def get_game_for_day(self, day: datetime.date) -> List[Game]:
        """Gets all games for the current day"""
        games = self.session.query(Game).filter(Game.date == day).all()
        return games


    def change_balance(self, user: User, amount_to_change: int):
        """Changes the balance of a user by a given amount"""
        new_balance = user.balance.balance_amount + amount_to_change
        if new_balance < 0:
            new_balance = 0
        user.balance.balance_amount = new_balance   
        self.session.commit()

    def place_wager(self, user: User, amount: int, outcome: Outcome) -> bool:
        """Places a wager on an outcome"""
        if user.balance.balance_amount < amount:
            return False
        wager = Wager(user_id=user.id, wager_amount=amount, outcome_id=outcome.id)
        self.session.add(wager)
        self.session.commit()
        return True
