import uvicorn
from fastapi import FastAPI, Request, status, Form, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import get_settings
from app.dependencies import IsUserLoggedIn, SessionDep, AuthDep
from fastapi.templating import Jinja2Templates
from app.utilities import get_flashed_messages
from jinja2 import Environment, FileSystemLoader
from sqlmodel import select
from app.models import Album, User, Track, Comment, Reaction
from app.utilities import flash, create_access_token
from fastapi.staticfiles import StaticFiles


app = FastAPI(middleware=[
    Middleware(SessionMiddleware, secret_key=get_settings().secret_key)
]
)
template_env = Environment(loader = FileSystemLoader("app/templates",), )
template_env.globals['get_flashed_messages'] = get_flashed_messages
templates = Jinja2Templates(env=template_env)
static_files = StaticFiles(directory="app/static")

app.mount("/static", static_files, name="static")


@app.get('/', response_class=RedirectResponse)
async def index_view(
  request: Request,
  user_logged_in: IsUserLoggedIn,
):
  if user_logged_in:
    return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)
  return RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login")
async def login_view(
  user_logged_in: IsUserLoggedIn,
  request: Request,
):
  if user_logged_in:
    return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)
  return templates.TemplateResponse(
          request=request, 
          name="login.html",
      )

@app.post('/login')
def login_action(
  request: Request,
  db: SessionDep,
  username: str = Form(),
  password: str = Form(),
):
  
  user = db.exec(select(User).where(User.username == username)).one_or_none()
  if user and user.check_password(password):
    response = RedirectResponse(url=request.url_for("index_view"), status_code=status.HTTP_303_SEE_OTHER)
    access_token = create_access_token(data={"sub": f"{user.id}"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=True,
    )    
    return response
  else:
    flash(request, 'Invalid username or password')
    return RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)


@app.get('/app')
def home_view(request: Request, db: SessionDep, user: AuthDep, album_id: int = None, track_id: int = None):
  albums = db.exec(select(Album)).all()
  
  selected_album = None
  if album_id:
      selected_album = db.get(Album, album_id)
  
  selected_track = None
  if track_id:
      selected_track = db.get(Track, track_id)

  return templates.TemplateResponse(
          request=request, 
          name="index.html",
          context={"albums": albums, "selected_album": selected_album, "selected_track": selected_track}
      )

@app.get('/logout')
async def logout(request: Request):
  response = RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)
  response.delete_cookie(
      key="access_token", 
      httponly=True,
      samesite="none",
      secure=True
  )
  flash(request, 'logged out')
  return response

@app.get('/view-albums', response_model=list[Album])
def view_all_albums(db:SessionDep): 
  listalbums = db.exec(select(Album)).all()
  return listalbums

@app.get('/tracks/{album_id}', response_model=list[Track], status_code=status.HTTP_200_OK)
async def list_tracks(db:SessionDep, album_id: int):
  album_tracks = db.exec(select(Track).where(Track.album_id == album_id)).all()

  if not album_tracks:
    raise HTTPException(
      status_code = status.HTTP_404_NOT_FOUND,
      detail = "Error, album not found or has no tracks"
    )
  
  return album_tracks

@app.post('/comments')
async def make_comment(db: SessionDep, track_id: int = Form(), album_id: int = Form(), comment_text: str = Form()):
  new_comment = Comment(track_id=track_id, album_id=album_id, comment=comment_text)
  try:
    db.add(new_comment)
    db.commit()
    # Redirect back to the home view with the current selection active
    return RedirectResponse(url=f"/app?album_id={album_id}&track_id={track_id}", status_code=status.HTTP_303_SEE_OTHER)
  except Exception:
    raise HTTPException(
      status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
      detail = "An error occurred while posting comment",
    )

@app.get('/comments/{track_id}', response_model=list[Comment], status_code=status.HTTP_200_OK)
def list_comments(db: SessionDep, track_id: int):
  track = db.get(Track, track_id)

  if not track:
    raise HTTPException(status_code=404, detail="Track not found")
  
  return track.comments

@app.post('/react', status_code = status.HTTP_200_OK)
def comment_react(db:SessionDep, reaction: int, id:int, albumid:int):
  album = db.exec(select(Album).where(Album.id == albumid)).first()
  if not album:
    raise HTTPException(
      status_code = status.HTTP_404_NOT_FOUND,
      detail = "Error, album not found"
    )
  track = db.exec(select(Track).where(Track.id == id)).first()
  if not track: 
    raise HTTPException(
      status_code = status.HTTP_404_NOT_FOUND,
      detail = "Error, track not found"
    )
  
  new_reaction = Reaction(track_id=id, album_id=albumid)
  try:
    db.add(new_reaction)
    db.commit()
    return "reaction saved"
  except Exception:
    db.rollback()
    raise HTTPException(
      status_code = 500,
      detail = "Error saving reaction"
    )


@app.delete('/comment/{trackid}', status_code=200)
def delete_comment(db:SessionDep, trackid:int, albumid:int):
  # This logic assumes you want to delete all comments for a specific track
  comments = db.exec(select(Comment).where(Comment.track_id == trackid)).all()

  try:
    for comment in comments:
        db.delete(comment)
    db.commit()
    return {"detail": "All comments for track deleted"}
  except Exception:
    db.rollback()
    raise HTTPException(
      status_code = 500,
      detail = "Error deleting comment"
    )
