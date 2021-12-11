
from flask import Flask, request, render_template, redirect, session, flash, make_response
from werkzeug.exceptions import BadRequestKeyError
from surveys import surveys
from flask_debugtoolbar import DebugToolbarExtension

RESPONSES = 'responses'
CURRENT_SURVEY = 'current_survey'

app = Flask(__name__)

app.config['SECRET_KEY'] = 'its-a-secret'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)


@app.route('/')
def survey_title():
    '''Show Pick a survey form'''

    return render_template('pick_survey.html', surveys=surveys)


@app.route('/', methods=['POST'])
def pick_survey():
    '''Select a survey to start'''
    survey_id = request.form['survey_code']

    # dont let the user re-take a survey until cookie times out
    if request.cookies.get(f'completed_{survey_id}'):
        return render_template('already_done.html')

    survey = surveys[survey_id]
    session[CURRENT_SURVEY] = survey_id

    return render_template('survey_title.html', survey=survey)


@app.route('/start', methods=["POST"])
def start_survey():
    '''begin the survey and display 1st question'''

    session[RESPONSES] = []

    return redirect('/questions/0')


@app.route('/answer', methods=['POST'])
def handle_question():
    '''Save user response and redirect to the next question'''
    choice = None
    #get the user's choice
    try:
        choice = request.form['answer']
    except BadRequestKeyError:
        flash('Please select an answer!', 'error')
        return redirect('/questions/0')

    text = request.form.get('text', "")

    # add this response to the list in the session
    responses = session[RESPONSES]
    responses.append({'choice': choice, 'text': text})

    # add current response to the session
    session[RESPONSES] = responses
    survey_code = session[CURRENT_SURVEY]
    survey = surveys[survey_code]

    if(len(responses) == len(survey.questions)):
        # user answered all questions, thank the user.
        return redirect('/complete')
    else:
        return redirect(f'/questions/{len(responses)}')


@app.route('/questions/<int:questID>')
def display_question(questID):
    '''Display the current question'''

    responses = session.get(RESPONSES)
    survey_code = session[CURRENT_SURVEY]
    survey = surveys[survey_code]

    if (responses is None):
        # if the user is trying to access question page too soon
        return redirect('/')

    if (len(responses) == len(survey.questions)):
        # User answered all questions, Thank them.
        return redirect('/complete')

    if(len(responses) != questID):
        # if Trying to access questions out of order - do not allow
        # flash(f'Invalid question id: {questID}.')
        return redirect(f'/questions/{len(responses)}')

    question = survey.questions[questID]
    return render_template('questions.html', question_num=questID, question=question)


@app.route('/complete')
def complete():
    '''Survey is complete, Thank the user and list the responses.'''
    survey_id = session[CURRENT_SURVEY]
    survey = surveys[survey_id]
    responses = session[RESPONSES]

    html = render_template('complete.html', survey=survey, responses=responses)

    #set the cookie so they can't redo the survey until it's done.
    response = make_response(html)
    response.set_cookie(f'completed_{survey_id}', 'yes', max_age=0)
    return response
    
