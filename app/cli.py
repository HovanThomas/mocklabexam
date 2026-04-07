import typer
from app.database import create_db_and_tables, get_cli_session, drop_all
from app.models import *
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.utilities import encrypt_password

cli = typer.Typer()

@cli.command()
def initialize():
    with get_cli_session() as db:
        drop_all() 
        create_db_and_tables() 
        
        bob = UserBase(username='bob', email='bob@mail.com', password=encrypt_password("bobpass"))
        bob_db = User.model_validate(bob)

        db.add(bob_db)
        db.commit()        

        Ablum1 = Album(album_name="Album1", user_id=bob_db.id)
        db.add(Ablum1)
        db.commit()

        track1 = Track(track_name="Track1", album_id=Ablum1.id, album=Ablum1)
        db.add(track1)
        db.commit()

        comment1 = Comment(comment="nice music, really like it", track_id=track1.id, album_id=Ablum1.id)
        db.add(comment1)
        db.commit()

        


        print("Database Initialized")

@cli.command()
def test():
    print("You're already in the test")


if __name__ == "__main__":
    cli()