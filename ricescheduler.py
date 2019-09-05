#!/usr/bin/env python

import re, sys, urllib2
import arrow # http://crsmithdev.com/arrow/
import pypandoc # https://github.com/bebraw/pypandoc
from bs4 import BeautifulSoup
from itertools import cycle
import calendar

def locale():
    return arrow.locales.get_locale('en_us')

def regex(keyword):
    return re.compile('(.*)' + keyword + '(.*)', re.DOTALL)

def make_url(semester, year): 
    ''' Takes semester and year as strings, returns url to calendar '''
    if semester == 'Fall' and year == '2019':
        term = 10
    elif semester == 'Spring' and year == '2020':
        term = 11
    elif semester == 'Fall' and year == '2020':
        term = 13
    baseurl = 'https://onestop.umn.edu/dates-and-deadlines?field_date_category_value=All&field_date_term_value='
    url = baseurl + str(term)
    return url

def date_formats():
    ''' based on Arrow string formats at http://crsmithdev.com/arrow/#tokens '''
    date_formats = [('Tuesday, January 12, 2016', 'dddd, MMMM D, YYYY'),
            ('Tuesday, January 12', 'dddd, MMMM D'),
            ('Tue., Jan. 12, 2016', 'ddd., MMM. D, YYYY'),
            ('Tue., Jan. 12', 'ddd., MMM. D'),
            ('January 12, 2016', 'MMMM D, YYYY'),
            ('January 12', 'MMMM D'),
            ('Jan. 12', 'MMM. D'),
            ('January 12 (Tuesday)', 'MMMM D (dddd)'),
            ('1/12', 'M/D'),
            ('01/12', 'MM/DD'),
            ('2016-01-12', 'YYYY-MM-DD')]
    return date_formats

def fetch_registrar_table(url):
    ''' Get academic calendar table from registrar website '''
    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find('table')

def range_of_days(start, end):
    return arrow.Arrow.range('day', start, end)

def clean_cell(td):
    ''' Remove whitespace from a registrar table cell '''
    return re.sub(r"\s+", "", td)

def parse_date(day):
    ''' Get date or date range as lists from cell in registrar's table '''
    abbr_to_num = {name: num for num, name in enumerate(calendar.month_abbr) if num}
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May',
            'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ms = [abbr_to_num[m] for m in months if m in day]
    ds = [int(d) for d in re.split('\D', day) if 0 < len(d) < 3]
    ys = [int(y) for y in re.split('\D', day) if len(y) == 4]
    dates = zip(cycle(ms), ds) if len(ds) > len(ms) else zip(ms, ds)
    dates = [arrow.get(ys[0], md[0], md[1]) for md in dates]
    if len(dates) > 1:
        return range_of_days(dates[0], dates[1])
    else:
        return dates

def parse_registrar_info(semesterYear):
    ''' Parse registrar table and return first, last, cancelled days of class as lists '''
    registrar_info_object  = open("schedules/" + semesterYear, "r")
    no_classes = []
    for line in registrar_info_object: 
        parsedLine = line.split("|")
        day = parse_date(parsedLine[0])
        event = parsedLine[1]
        if re.match(regex('sessions begin'), event):
            first_day = day
        if re.match(regex('Last day of instruction'), event):
            last_day = day
        if re.match(regex('University closed'), event) or re.match(regex('Spring break'), event):
            for date in day:
                no_classes.append(date)
            

    return first_day, last_day, no_classes
    
def sorted_classes(weekdays, first_day, last_day, no_classes):
    ''' Take class meetings as list of day names, return lists of Arrow objects '''
    semester = range_of_days(first_day[0], last_day[0])
    possible_classes = [d for d in semester if locale().day_name(d.isoweekday()) in weekdays]
    return possible_classes, no_classes

def schedule(possible_classes, no_classes, show_no=None, fmt=None):
    ''' Take lists of Arrow objects, return list of course meetings as strings '''
    course = []
    date_format = fmt if fmt else 'dddd, MMMM D, YYYY'
    
    for d in possible_classes:
        if d not in no_classes:
            course.append(d.format(date_format))
        elif show_no:
            course.append(d.format(date_format) + ' - NO CLASS')
    return course

def markdown(schedule, semesterYear, templatedir):
    course = ['## ' + d + '\n' for d in schedule]
    course = [d + '[Fill in class plan]\n\n' if 'NO CLASS' not in d else d for d in course]
    md_args = ['--template=' + templatedir + '/syllabus.md', '--to=markdown',
            '--variable=semesterYear:' + semesterYear.capitalize()]
    return pypandoc.convert('\n'.join(course), 'md', 'md', md_args)

def output(schedule, semesterYear, fmt, templatedir, outfile):
    md = markdown(schedule, semesterYear, templatedir)
    template = templatedir + '/syllabus.' + fmt if templatedir else ""
    if fmt == 'docx':
        template_arg = '--reference-doc=' + template
    else:
        template_arg = '--template=' + template
    pandoc_args = ['--standalone']
    pandoc_args.append(template_arg)
    output = pypandoc.convert(md, fmt, 'md', pandoc_args, outputfile=outfile)
    assert output == ''
