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
        
        bob = User(username='bob', email='bob@mail.com', password=encrypt_password("bobpass"))
        db.add(bob)
        db.commit()        
        db.refresh(bob)

        album1 = Album(album_name="Album1", user_id=bob.id, image_url="https://weblabs.web.app/api/brainrot/1.webp")
        db.add(album1)
        db.commit()
        db.refresh(album1)

        track1 = Track(track_name="Track1", album_id=album1.id, image_url="https://weblabs.web.app/api/brainrot/2.webp")
        db.add(track1)
        db.commit()
        db.refresh(track1)

        comment1 = Comment(comment="nice music, really like it", track_id=track1.id, album_id=album1.id)
        db.add(comment1)
        db.commit()

        


        print("Database Initialized")

@cli.command()
def test():
    print("You're already in the test")


if __name__ == "__main__":
    cli()