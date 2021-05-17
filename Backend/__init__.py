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
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
      response.headers.add('Access-Control-Allow-Methods', 'GET, PATCH, POST, DELETE, OPTIONS')
      return response

    @app.route('/questions', methods=['GET'])
    def get_questions():
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      categories = Category.query.all()
      categories_dict = {}
      for category in categories:
          categories_dict[category.id] = category.type

      if len(current_questions) == 0:
          abort(404)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'totalQuestions': len(Question.query.all()),
        'categories': categories_dict,
        'currentCategory': None
      })

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_specific_category(category_id):
        try:
            category = Category.query.filter(Category.id == category_id).one_or_none()
            if category is None:
                abort(404)

            questions = Question.query.filter(Question.category == str(category_id)).all()
            if len(questions) == 0:
                abort(404)

            current_questions = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'totalQuestions': len(questions),
                'currentCategory': category.format()
                })
        except:
            abort(404)


    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        return jsonify({
            'success': True,
            'categories': categories_dict
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        try:
            question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
            question.insert()

            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all()),
                'current_category': question.category
            })

        except:
            abort(405)

    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_term = body.get('searchTerm', None)

        try:
            if search_term:
                selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search_term)))
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection.all()),
                    'current_category': None
                    })
        except:
            abort(400)

    '''
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()
        if not body:
            abort(400)

        previous_questions = body.get('previous_questions', None)
        category_id = body.get('quiz_category', None)

        if category_id['id'] == 0:
            if previous_questions is not None:
                questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
            else:
                questions = Question.query.all()

        else:
            if previous_questions is not None:
                questions = Question.query.filter(Question.id.notin_(previous_questions), Question.category==category_id['id']).all()

            else:
                questions = Question.query.filter(Question.category==category_id['id']).all()

        next_question = random.choice(questions).format()
        if not next_question:
            abort(404)

        if next_question is None:
            next_question = False

        return jsonify({
            'success': True,
            'question': next_question
        })


    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(400)
    def unable_loading(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Unable to load questions. Please try your request again"
        }), 400

    @app.errorhandler(405)
    def wrong_url(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Wrong URL."
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable."
        }), 422

    return app
