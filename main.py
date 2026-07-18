from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import models
from models import Movies
from typing import Annotated, Optional
from database import engine, SessionLocal
from fastapi.responses import JSONResponse

app = FastAPI()

# Creating table
models.Base.metadata.create_all(bind=engine) 

class Movie(BaseModel):
    movie_id: int
    title: str
    director: str = Field(max_length=100)
    genre: str = Field(max_length=150)
    duration: int  
    rating: float 

class Movieupdate(BaseModel):
    title: Optional[str] = Field(default=None)
    director: Optional[str] = Field(default=None, max_length=100)
    genre: Optional[str] = Field(default=None, max_length=150)
    duration: Optional[int] = Field(default=None) 
    rating: Optional[float] = Field(default=None)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get('/movies')
def read_movies(db: db_dependency):
    return db.query(Movies).all()


@app.get('/movies/{movie_id}')
def read_specific_movies(db: db_dependency, movie_id: int):

    specific_movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    
    if specific_movie is not None:
        return specific_movie
    else:
        raise HTTPException(status_code=404, detail='Movie not found')
    

@app.post('/create_movies/')
def create_movies(db: db_dependency, new_movie: Movie):
    movie_model = Movies(**new_movie.model_dump())
    db.add(movie_model)
    db.commit()

    return JSONResponse(status_code=201, content={'message': 'Movie created successfully'})


@app.put('/movies/{movie_id}')
def update_specific_movies(db: db_dependency, movie_id: int, update_movie: Movieupdate):

    movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    
    if movie is None:
        raise HTTPException(status_code=404, detail='Movie not found')
    
    update_data = update_movie.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    db.commit()

    return JSONResponse(status_code=200, content={'message': 'Movie updated successfully'})


@app.delete('/movies/{movie_id}')
def delete_movies(db: db_dependency, movie_id: int):

    movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    
    if movie is None:
        raise HTTPException(status_code=404, detail='Movie not found')
    
    db.query(Movies).filter(Movies.movie_id == movie_id).delete()
    db.commit()

    return JSONResponse(status_code=200, content={'message': 'Movie deleted successfully'})