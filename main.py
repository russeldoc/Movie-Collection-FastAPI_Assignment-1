from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import models
from models import Movies
from typing import Annotated, Optional, Literal
from database import engine, SessionLocal
from fastapi.responses import JSONResponse
from sqlalchemy import asc, desc

app = FastAPI()

# Creating database table

models.Base.metadata.create_all(bind=engine) 

# Pydantic Model

class Movie(BaseModel):
    movie_id: int
    title: str
    director: str = Field(max_length=100)
    genre: Literal["action", "comedy", "drama", "thriller"]
    duration: int = Field(gt=0)
    rating: float = Field(ge=0, le=5)


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    director: Optional[str] = Field(default=None, max_length=100)
    genre: Optional[Literal["action", "comedy", "drama", "thriller"]] = None
    duration: Optional[int] = Field(default=None, gt=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# get all movies
@app.get('/movies')
def read_movies(db: db_dependency):
    return db.query(Movies).all()

# Sort Movies
@app.get("/movies/sort")
def view_sorted_movies(
    db: db_dependency,
    sort_by: str = Query(
        "rating",
        description="Sort by duration or rating"
    ),
    order: str = Query(
        "desc",
        description="Choose asc or desc"
    )
):

    valid_fields = ["duration", "rating"]

    if sort_by not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field. Choose from {valid_fields}"
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Order must be either 'asc' or 'desc'"
        )

    column = getattr(Movies, sort_by)

    if order == "asc":
        movies = db.query(Movies).order_by(asc(column)).all()
    else:
        movies = db.query(Movies).order_by(desc(column)).all()

    return movies

# get single movie
@app.get('/movies/{movie_id}')
def get_movies(db: db_dependency, movie_id: int):

    specific_movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    
    if specific_movie is not None:
        return specific_movie
    else:
        raise HTTPException(status_code=404, detail='Movie not found')
    
# Create movie
@app.post('/create_movies/')
def create_movies(db: db_dependency, new_movie: Movie):
    movie_model = Movies(**new_movie.model_dump())
    db.add(movie_model)
    db.commit()

    return JSONResponse(status_code=201, content={'message': 'Movie created successfully'})

# Update movie
@app.put('/movies/{movie_id}')
def update_specific_movies(db: db_dependency, movie_id: int, update_movie: MovieUpdate):

    movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    
    if movie is None:
        raise HTTPException(status_code=404, detail='Movie not found')
    
    update_data = update_movie.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    db.commit()

    return JSONResponse(status_code=200, content={'message': 'Movie updated successfully'})

# Delete Movie
@app.delete('/movies/{movie_id}')
def delete_movies(db: db_dependency, movie_id: int):

    movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    
    if movie is None:
        raise HTTPException(status_code=404, detail='Movie not found')
    
    db.query(Movies).filter(Movies.movie_id == movie_id).delete()
    db.commit()

    return JSONResponse(status_code=200, content={'message': 'Movie deleted successfully'})



