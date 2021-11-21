import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET, POST, PATCH, PUT, DELETE, OPTIONS')
        return response

    @app.route('/categories')
    def get_categories():
        categories = {
            category.id: category.type for category in Category.query.all()}

        if len(categories) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "categories": categories,
            "total_categories": len(categories)
        })

    @app.route('/questions')
    def get_questions():
        categories = Category.query.all()
        formatted_categories = {
            category.id: category.type for category in categories}
        selection = Question.query.all()
        questions = paginate_questions(request, selection)

        if len(questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'current_category': None,
            'categories': formatted_categories,
            'questions': questions,
            'total_questions': len(selection)
        })

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.filter(Question.id == id).one_or_none()

            question.delete()

            return jsonify({
                'success': True,
                'deleted': id,
                'total_questions': len(Question.query.all())
            })
        except BaseException:
            if question is None:
                abort(404)
            else:
                abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():

        try:
            body = request.get_json()

            question = body.get('question', None)
            answer = body.get('answer', None)
            difficulty = body.get('difficulty', None)
            category = body.get('category', None)
            search = body.get('searchTerm', None)

            if search:
                selection = Question.query.filter(
                    Question.question.ilike(
                        '%{}%'.format(search))).all()
                questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': questions,
                    'total_questions': len(selection)
                })

            else:

                new_question = Question(
                    question=question,
                    answer=answer,
                    difficulty=difficulty,
                    category=category
                )

                new_question.insert()

                return jsonify({
                    'success': True,
                    'created': new_question.id,
                    'total_questions': len(Question.query.all())
                })

        except BaseException:
            abort(422)

    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):
        try:
            current_category = Category.query.get(id).format()
            selection = Question.query.filter(Question.category == id)
            questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(selection.all()),
                'current_category': current_category
            })

        except BaseException:
            if id not in [category.id for category in Category.query.all()]:
                abort(404)
            else:
                abort(422)

    # route to handle quiz playing
    @app.route('/quizzes', methods=['POST'])
    def get_quiz_question():

        try:
            body = request.get_json()
            previous_questions = body.get('previous_questions', None)
            current_category = body.get('quiz_category', None)

            if current_category is None:
                abort(422)

            # select questions from all categories
            if current_category['id'] == 0:
                selection = Question.query.all()

            # select questions from current category
            else:
                selection = Question.query.filter(
                    Question.category == current_category['id']).all()

            # excluding previous questions from pool of choice
            previous_questions_ids = [
                question for question in previous_questions]
            total_ids = [question.format()['id'] for question in selection]
            available_ids = [
                id for id in total_ids if id not in previous_questions_ids]

            # ending the game if there are no more questions in the category
            if len(available_ids) == 0:
                return jsonify({
                    'success': True
                })

            # getting a random question from remaining ones
            new_question_id = random.choice(available_ids)

            new_question = Question.query.get(new_question_id).format()

            return jsonify({
                'success': True,
                'question': new_question
            })

        except BaseException:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return (jsonify({"success": False, "error": 404,
                         "message": "resource not found"}), 404, )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422,
                     "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400,
                       "message": "bad request"}), 400

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": 500,
                       "message": "internal server error"}), 500

    return app
