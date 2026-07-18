
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from pydantic import BaseModel, Field
from typing import Annotated, Optional, Literal

import models
from models import Movies
from database import engine, SessionLocal

app = FastAPI()

# Create database table
models.Base.metadata.create_all(bind=engine)


# -----------------------------
# Pydantic Models
# -----------------------------
class MovieCreate(BaseModel):
    movie_id: int
    title: str
    director: str = Field(max_length=100)
    genre: Literal["action", "comedy", "drama", "thriller"]
    duration: int = Field(gt=0)
    rating: float = Field(ge=0, le=5)


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    director: Optional[str] = Field(default=None, max_length=100)
    genre: Optional[
        Literal["action", "comedy", "drama", "thriller"]
    ] = None
    duration: Optional[int] = Field(default=None, gt=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)


# -----------------------------
# Database Dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# -----------------------------
# Get All Movies
# -----------------------------
@app.get("/movies")
def read_movies(db: db_dependency):
    return db.query(Movies).all()


# -----------------------------
# Get Single Movie
# -----------------------------
@app.get("/movies/{movie_id}")
def get_movie(movie_id: int, db: db_dependency):

    movie = db.query(Movies).filter(
        Movies.movie_id == movie_id
    ).first()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie not found"
        )

    return movie


# -----------------------------
# Create Movie
# -----------------------------
@app.post("/create_movies", status_code=status.HTTP_201_CREATED)
def create_movie(
    new_movie: MovieCreate,
    db: db_dependency
):

    existing_movie = db.query(Movies).filter(
        Movies.movie_id == new_movie.movie_id
    ).first()

    if existing_movie:
        raise HTTPException(
            status_code=400,
            detail="Movie ID already exists"
        )

    movie_model = Movies(**new_movie.model_dump())

    db.add(movie_model)
    db.commit()
    db.refresh(movie_model)

    return movie_model


# -----------------------------
# Update Movie
# -----------------------------
@app.put("/movies/{movie_id}")
def update_movie(
    movie_id: int,
    update_movie: MovieUpdate,
    db: db_dependency
):

    movie = db.query(Movies).filter(
        Movies.movie_id == movie_id
    ).first()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie not found"
        )

    update_data = update_movie.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    db.commit()
    db.refresh(movie)

    return movie


# -----------------------------
# Delete Movie
# -----------------------------
@app.delete("/movies/{movie_id}")
def delete_movie(
    movie_id: int,
    db: db_dependency
):

    movie = db.query(Movies).filter(
        Movies.movie_id == movie_id
    ).first()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie not found"
        )

    db.delete(movie)
    db.commit()

    return {
        "message": "Movie deleted successfully"
    }


# -----------------------------
# Sort Movies
# -----------------------------
@app.get("/movies/sort")
def view_sorted_movies(
    db: db_dependency,
    sort_by: Literal["duration", "rating"] = Query(
        default="rating",
        description="Sort by duration or rating"
    ),
    order: Literal["asc", "desc"] = Query(
        default="desc",
        description="Choose sorting order"
    )
):

    column = getattr(Movies, sort_by)

    if order == "asc":
        movies = db.query(Movies).order_by(
            asc(column)
        ).all()
    else:
        movies = db.query(Movies).order_by(
            desc(column)
        ).all()

    return movies
