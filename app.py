import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_ENDPOINT = "https://api.themoviedb.org/3/search/movie"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQL_ALCHEMY_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Bootstrap(app)


class TitleForm(FlaskForm):
    movie_title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


class EditForm(FlaskForm):
    your_rating = StringField(label="Your Rating out of 10 e.g. 7.5", validators=[DataRequired()])
    your_review = StringField(label="You Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


@app.route('/')
def movies():
    all_movies = Movies.query.order_by(Movies.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    title_form = TitleForm()
    if request.method == "GET":
        return render_template("add.html", form=title_form)
    elif request.method == "POST":
        movie_title = request.form["movie_title"]
        parameters = {
            "api_key": API_KEY,
            "query": movie_title
        }
        movies_details = requests.get(url=API_ENDPOINT, params=parameters).json()["results"]
        return render_template("select.html", movies=movies_details)


@app.route("/movie", methods=["GET", "POST"])
def search_movie():
    movie_id = request.args["movie_id"]
    api_key = os.getenv("API_KEY")
    parameters = {
        "api_key": api_key,
    }
    movie_details = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_id}", params=parameters).json()
    movie_img = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_id}/images", params=parameters).json()
    movie_title = movie_details['title']
    movie_description = movie_details['overview']
    movie_release_year = movie_details['release_date'].split('-')[0]
    movie_poster_url = f"https://image.tmdb.org/t/p/w500/{movie_img['posters'][0]['file_path']}"
    movie = Movies(
        title=movie_title,
        year=movie_release_year,
        description=movie_description,
        rating=1.0,
        ranking=1,
        review="My favourite character was the caller.",
        img_url=movie_poster_url
    )
    db.session.add(movie)
    db.session.commit()
    movie_id = Movies.query.filter_by(title=movie_title).first()
    return redirect(url_for("edit_rating_and_review", id=movie_id.id))


@app.route("/edit", methods=["GET", "POST"])
def edit_rating_and_review():
    form = EditForm()
    if request.method == "GET":
        movie_id = request.args.get("id")
        movie_title = Movies.query.filter_by(id=movie_id).first()
        return render_template("edit.html", form=form, title=movie_title.title, id=movie_id)
    elif form.validate_on_submit():
        movie_id = request.args.get("id")
        movie_to_update = Movies.query.get(movie_id)
        movie_to_update.rating = request.form["your_rating"]
        movie_to_update.review = request.form["your_review"]
        db.session.commit()
        return redirect(url_for("movies"))


@app.route("/delete", methods=["GET"])
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movies.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("movies"))


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")
