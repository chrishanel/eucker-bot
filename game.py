from venv import create
from sqlalchemy.orm import Session
import sqlalchemy as db
from db import *

def get_or_create_user(discord_user_id: str) -> User:
    stmt = db.select(User).where(User.discord_id == discord_user_id)
    result = session.execute(stmt).first()
    if result:
        return result
    
    return create_user(discord_user_id)


def create_user(discord_user_id: str) -> User:
    user = User(discord_id=discord_user_id)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


if __name__ == "__main__":
   print(get_or_create_user("hello")) 