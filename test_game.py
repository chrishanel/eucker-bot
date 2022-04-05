import os
os.environ['DB_CONN_URI'] = 'sqlite:///test.db'
import pytest
from game import BattlegroundGame
import db
@pytest.fixture(scope="session", autouse=True)
def game():
    game = BattlegroundGame("sqlite:///test.db")
    db.main()
    from pipeline import scrape_data, update_db
    scrape_data.main()
    update_db.main()
    yield game
    game._close_db()
    try:
        os.remove("test.db")    
    except:
        pass

def test_get_balance_of_user(game):
    u = game.get_or_create_user("test")
    balance = u.balance
    assert balance.balance_amount == 0
    
def test_get_days_games(game):
    games = game.get_todays_games()
    assert len(games) > 0 
