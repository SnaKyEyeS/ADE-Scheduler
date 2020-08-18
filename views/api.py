from flask import current_app as app
from flask import Blueprint, jsonify, request, session, redirect, url_for

import backend.schedules as schd


api = Blueprint('api', __name__, static_folder='../static')


@api.route('/schedule', methods=['GET'])
def get_schedule():
    """
    API endpoint to fetch the schedule matching the various arguments.

    The request accepts 3 arguments:
     - view: if set to True, shows the schedule in ADE-Scheduler's schedule viewer.
             By default, view = False the data is returned in JSON format.
     - year: defines the academical year. Accepted format is YYYY-YYYY where the second year is the first + 1.
             e.g.: 2020-20201
     - code: the various code of the courses to be added to the schedule.
             e.g.: LELEC2885, LMECA2170, LEPL1104,...
             To specify a list of codes, use the following format:
             /schedule?code=CODE_1&code=CODE_2&code=CODE_3 and so on.

    Example:
        https://ade-scheduler.info.ucl.ac.be/schedule?year=2020-2021&code=LMECA2170&code=LEPL1104&view=true
    """
    mng = app.config['MANAGER']

    year = request.args.get('year')
    codes = request.args.getlist('code')
    view = bool(request.args.get('view'))

    project_id = mng.get_project_ids(year=year)
    if project_id is None:
        project_id = mng.get_default_project_id()

    schedule = schd.Schedule(project_id=project_id)
    schedule.add_course([code.upper() for code in codes])

    if view:
        session['current_schedule'] = schedule
        return redirect(url_for('calendar.index'))

    return jsonify({
        'events': ['hey :D'],
    }), 200
