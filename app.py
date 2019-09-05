#!/usr/bin/env python

import os
from arrow import get
from flask import Flask, render_template, request, url_for, send_file, send_from_directory
from tempfile import NamedTemporaryFile
from ricescheduler import make_url, sorted_classes, schedule, output, date_formats, parse_registrar_info, locale

app = Flask(__name__)

@app.route('/')
def form():
    years = [str(y) for y in range(2019,2021)]
    months = ['January', 'February', 'March', 'April', 'May',
            'June', 'July', 'August', 'September', 'October', 'November', 'December']
    ddays = [str(d) for d in range(1,32)]
    formats = [t[0] for t in date_formats()]
    return render_template('form_submit.html', years=years, months=months, ddays=ddays, formats=formats)

@app.route('/generic/', methods=['GET'])
def generic():
    years = [str(y) for y in range(2019,2021)]
    months = ['January', 'February', 'March', 'April', 'May',
            'June', 'July', 'August', 'September', 'October', 'November', 'December']
    ddays = [str(d) for d in range(1,32)]
    formats = [t[0] for t in date_formats()]
    return render_template('form_submit_generic.html', years=years, months=months, ddays=ddays, formats=formats)

@app.route('/results/', methods=['POST'])
def results():

    semesterYear = request.form['semesterYear']
    weekdays = request.form.getlist('days')
    date_fmt = [b for (a, b) in date_formats() if a == request.form['format']][0]
    output_fmt = request.form['output']

    first_day, last_day, no_classes = parse_registrar_info(semesterYear)
    possible_classes, no_classes = sorted_classes(weekdays, first_day, last_day, no_classes)
    course = schedule(possible_classes, no_classes, show_no=True, fmt=date_fmt) 

    if output_fmt == 'plain':
        return '<br/>'.join(course)
    else:
        suffix = '.' + output_fmt
        templatedir = os.path.dirname(os.path.abspath(__file__)) + '/templates'
        tf = NamedTemporaryFile(suffix=suffix)
        output(course, semesterYear, output_fmt, templatedir=templatedir, outfile=tf.name)
        filename = semesterYear + 'Syllabus' + suffix
        return send_file(tf.name, attachment_filename=filename, as_attachment=True)

@app.route('/classes/', methods=['POST'])
def classes():

    year = int(request.form['year'])
    start_month = locale().month_number(request.form['start-month'])
    start_day = int(request.form['start-day'])
    last_month = locale().month_number(request.form['last-month'])
    last_day = int(request.form['last-day'])
    weekdays = request.form.getlist('days')
    date_fmt = [b for (a, b) in date_formats() if a == request.form['format']][0]

    try:
        start_date = [get(year, start_month, start_day)]
    except:
        return "The starting date you specified does not exist." 

    try:
        last_date = [get(year, last_month, last_day)]
    except:
        return "The ending date you specified does not exist." 

    possible_classes, no_classes = sorted_classes(weekdays, start_date, last_date, no_classes=[])
    course = schedule(possible_classes, no_classes, show_no=True, fmt=date_fmt) 
    return '<br/>'.join(course)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)

@app.route('/img/<path:path>')
def send_img(path):
    return send_from_directory('img', path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
