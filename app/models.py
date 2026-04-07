from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pydantic import EmailStr
from pwdlib import PasswordHash

class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    def check_password(self, plaintext_password:str):
        return PasswordHash.recommended().verify(password=plaintext_password, hash=self.password)
    
class Track(SQLModel, table=True):
    id: Optional[int] = Field(primary_key = True, default=None)
    album_id: Optional[int] = Field(foreign_key = "album.id")
    track_name: str  
    image_url: Optional[str] = Field(default=None)

    album: Optional["Album"] = Relationship(back_populates="tracks")
    comments: List["Comment"] = Relationship(back_populates="track")
    reactions: List["Reaction"] = Relationship(back_populates="track")

class Album(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key = "user.id")
    album_name: str = Field(index = True, unique = True)
    image_url: Optional[str] = Field(default=None)

    tracks: List[Track] = Relationship(back_populates="album")

class Comment(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    track_id: int = Field(foreign_key = "track.id")
    album_id: int = Field(foreign_key = "album.id")
    comment: str

    track: Optional[Track] = Relationship(back_populates="comments")

class Reaction(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    track_id: int = Field(foreign_key="track.id")
    album_id: int = Field(foreign_key="album.id")

    track: Optional[Track] = Relationship(back_populates="reactions")
