from pathlib import Path
from flask import Blueprint, Response, jsonify, request
from blueprints.shared import PARSERS
from lib.files import handle_file_upload
from lib.mdbook import questions_to_toml
from models import Generation, Question
from db import db

# routes for JSON API-based Flask app
api = Blueprint("api", __name__, template_folder="templates")


# handle file upload
@api.route("/", methods=["POST"])
def upload():
    # save uploaded file
    filename, unique_filename = handle_file_upload()

    # create generation instance in database
    generation = Generation(filename=filename, unique_filename=unique_filename)
    db.session.add(generation)
    db.session.commit()

    # run completion, add generated questions to database
    parser = PARSERS[request.form["book"]]
    generation.add_questions(parser)

    return {
        "message": f"Completed generation for {filename}"
    }


# return all generations as JSON
@api.route("/generated/all")
def all_generated():
    generations = Generation.query.all()

    return jsonify(generations)

# return generated items as JSON
@api.route("/generated/<generation_id>")
def score(generation_id):
    generation = db.get_or_404(Generation, generation_id)

    return jsonify(generation)


# reroll an item's distractors
@api.route("/question/<question_id>/reroll", methods=["POST"])
def reroll(question_id):
    question: Question = db.get_or_404(Question, question_id)
    question.reroll()

    return {
        "message": "Rerolled question's distractors"
    }


# generate new item from custom question and answer
@api.route("/generated/<generation_id>/new", methods=["POST"])
def new_item(generation_id):
    generation = db.get_or_404(Generation, generation_id)

    # TODO: avoid having to instantiate with empty options
    question = Question(
        generation_id=generation.id,
        question=request.form["question"],
        correct_answer=request.form["answer"],
        option1="",
        option2="",
        option3="",
        shard=0, # TODO: this should not default to the first shard
        score=0,
    )
    db.session.add(question)

    # add distractors to custom question
    question.reroll()
    db.session.commit()

    return {
        "message": "Created custom item"
    }


# delete a generated item
@api.route("/question/<question_id>/delete", methods=["POST"])
def delete(question_id):
    question = db.get_or_404(Question, question_id)

    db.session.delete(question)
    db.session.commit()

    return {
        "message": "Deleted question"
    }


# download mdbook-quiz TOML file
@api.route("/generated/<generation_id>/toml")
def download_toml(generation_id):
    generation = db.get_or_404(Generation, generation_id)
    toml = questions_to_toml(generation.questions)
    filename = Path(generation.filename).stem

    return Response(
        toml,
        mimetype="text/plain",
        headers={ "Content-disposition": f"attachment; filename={filename}-{generation_id}.toml" }
    )
