from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators, IntegerField, FloatField
from wtforms.validators import DataRequired
import requests
import os, requests, ast
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(50)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie.db"
db = SQLAlchemy(app)

API_KEY = os.getenv('API_KEY')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(80), nullable=False)
    img_url = db.Column(db.String(150), nullable=False)


class EditRatingForm(FlaskForm):
    rating = FloatField(
        label="Your Rating",
        render_kw={'placeholder': 'Your rating out of 10, ex.7.5'},
        validators=[validators.DataRequired(), validators.NumberRange(min=1, max=10)]
    )
    review = StringField(
        label="Your Review",
        render_kw={'placeholder': 'Insert Review, max 250 character'},
        validators=[validators.Optional(), validators.Length(max=250)]
    )
    submit = SubmitField(label="Done")


class AddMovieForm(FlaskForm):
    movie_title = StringField(label="Movie Title", validators=[validators.DataRequired()])
    submit = SubmitField(label="Add")


@app.route("/create_movie_list")
def create_movie_list():
    edit_form = EditRatingForm()
    movie = ast.literal_eval(request.args.get("movie_detail"))  # string to dictionary
    new_movie = Movie(
        id=movie['id'],
        title=movie['title'],
        img_url=f"https://image.tmdb.org/t/p/{movie['poster_path']}",
        year=movie['release_date'].split("-")[0],
        description=movie['overview'],
        rating=0.0,
        ranking=0,
        review=" ",
    )
    db.session.add(new_movie)
    db.session.commit()
    return render_template("edit.html", form=edit_form, movie=movie)


@app.route("/delete", methods=['GET', 'POST'])
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


def movie_list():
    return Movie.query.order_by(Movie.rating.desc())  # to order the movie


@app.route("/")
def home():
    movies = movie_list()
    i = 1
    for movie in movies:
        movie.ranking = i
        i += 1
        db.session.commit()
    return render_template("index.html", movies_db=movies)


# Using Quick-form
@app.route("/edit_rating/", methods=['GET', 'POST'])
def edit_rating():
    edit_form = EditRatingForm()
    movie_id = request.args.get("id")    # *** look at below description
    movie = Movie.query.get(movie_id)
    if edit_form.validate_on_submit():
        movie.rating = edit_form.rating.data
        if len(edit_form.review.data) != 0:
            movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=edit_form, movie=movie)

# *** If u are not use this, then add the id as the input at the method arguments
# example
# @app.route("/edit_rating/<int:id>", methods=['GET','POST'])
# def edit_rating(id):
#     edit_form = EditRatingForm()
#     movie_id = request.args.get("id")    # not used anymore
#     movie = Movie.query.get(id)
#     if edit_form.validate_on_submit():
#         movie.rating = edit_form.rating.data
#         movie.review = edit_form.review.data
#         db.session.commit()
#         return redirect(url_for('home'))
#     return render_template("edit.html", form=edit_form, movie=movie)


@app.route("/add-movie", methods=['GET', 'POST'])
def add_movie():
    add_movie_form = AddMovieForm()

    if add_movie_form.validate_on_submit():
        title = add_movie_form.movie_title.data
        parameters = {
            "api_key": API_KEY,
            "query": title,
            "page": 10
        }
        response = requests.get(url="https://api.themoviedb.org/3/search/movie", params=parameters)
        content = response.json()
        result = content['results']
        return render_template("select.html", movie_list=result)

    return render_template("add.html", form=add_movie_form)
    

if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()
    #     create_movie_list()


    app.run(debug=True)
