import datetime
import json

import flask
import pygal
from flask import Flask, render_template, request
from flask_cors import CORS

from client.lrs_client import get_statements
from config.dashboard_config import get_config
from filter.base_filter import filter_by_correct_score, \
    filter_by_incorrect_score, filter_by_table, filter_by_time_interval, filter_by_category, \
    filter_by_element, filter_by_exclusion_list, filter_by_verb, filter_by_session_id, filter_by_session_list, \
    filter_by_valid_session_id

app = Flask(__name__)

cors = CORS(app, resources={r"/static/*": {"origins": "*"}})

# Define shared variables
cache = dict()

general_infos = dict()

warnings = []


@app.route("/")
def controller_home():
    """
    Main route, will always be called, besides when getting a fullsize chart.
    :return: render template from templates folder, parameters represent model from MVC pattern
    """
    # Clear all warnings at begin
    warnings.clear()
    # Setup variables for later
    xapi_base_uri = 'http://ddigames.inf.tu-dresden.de/matching-games/'
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    game = request.args.get('game', '')
    screen = request.args.get('screen', '')
    # Check if user selected sessions
    selected_sessions = parse_sessions(request_args=request.args)
    chart_global = ""
    chart_time = ""
    charts_word = []
    charts_regex = []
    word_category_charts_absolute = []
    word_category_chart_relative = []
    # If nothing is filled out, show only form
    if start == '' and end == '' and game == '':
        return render_template('index.html')
    # Check if form was filled out completely
    if start == '' or end == '' or game == '':
        return render_template('index.html', start=start, end=end,
                               error="Bitte alle Felder des Formulars ausfüllen.")
    # Time on LRS Server is in GMT, time in Germany is GMT+1, so we have to subtract one hour.
    start_lrs = (datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M") - datetime.timedelta(hours=1)).strftime(
        "%Y-%m-%dT%H:%M")
    end_lrs = (datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M") - datetime.timedelta(hours=1)).strftime(
        "%Y-%m-%dT%H:%M")
    # Add game name to xAPI base URI to access data fields later
    xapi_base_uri += game + '/'
    # If no sessions were selected, show the list of sessions to the user
    if start != '' and selected_sessions == [] and game != '':
        statements = get_or_update_cache(start_lrs, end_lrs, xapi_base_uri)
        if len(statements) == 0:
            return render_template('index.html', start=start, end=end,
                                   error="Keine Interaktionen gefunden, entweder der LRS ist nicht verfügbar oder zur "
                                         "Zeitangabe gab es keine Spiele.")
        sessions, session_count = get_session_ids(statements, xapi_base_uri)
        return render_template('index.html', start=start, end=end, sessions=sessions, session_count=session_count,
                               game=game)
    # When sessions were selected, we can show charts
    if start != '' and selected_sessions != '' and game != '':
        statements = get_or_update_cache(start_lrs, end_lrs, xapi_base_uri)
        # We have to filter first for valid session ids, otherwise filtering for selected IDs will fail.
        filtered_valid = filter_by_valid_session_id(statement_list=statements, xapi_base_uri=xapi_base_uri)
        filter_sessions = filter_by_session_list(statement_list=filtered_valid, session_list=selected_sessions,
                                                 xapi_base_uri=xapi_base_uri)
        update_general_infos(selected_sessions=selected_sessions, statements=filter_sessions,
                             xapi_base_uri=xapi_base_uri)
        # Get only scored elements to analyze them later
        filtered_scored = filter_by_verb(statement_list=filter_sessions, verb='scored')

        tables = general_infos[str(selected_sessions)]["tables"]
        levels = general_infos[str(selected_sessions)]["levels"]

        chart_global = general_chart(filtered_scored, tables, xapi_base_uri)

        chart_time = time_frame_chart(filtered_scored, xapi_base_uri, tables)

        word_list = aggregate_all_words(levels=levels, selected_sessions=selected_sessions)

        regex_list = aggregate_all_regex(levels=levels, selected_sessions=selected_sessions)

        charts_word = false_words_charts(regex_list=regex_list, word_list=word_list,
                                         filtered_scored=filtered_scored, xapi_base_uri=xapi_base_uri, tables=tables)
        charts_regex = false_regex_charts(regex_list=regex_list, word_list=word_list,
                                          filtered_scored=filtered_scored, xapi_base_uri=xapi_base_uri, tables=tables)

        word_category_charts_absolute = word_charts_absolute(xapi_base_uri, filtered_scored,
                                                             tables, word_list=word_list)
        word_category_chart_relative = word_chart_relative(xapi_base_uri, filtered_scored, tables, word_list)
    return render_template('index.html', start=start, chart_global=chart_global, end=end, screen=screen, game=game,
                           chart_time=chart_time, charts_regex=charts_regex,
                           charts_word=charts_word, word_category_charts_absolute=word_category_charts_absolute,
                           word_category_chart_relative=word_category_chart_relative, warnings=warnings)


@app.route("/chart")
def controller_chart():
    """
    Chart route to display fullsize charts, expects a chart in base64 as a request argument.
    :return: render the chart template from the templates folder
    """
    chart = request.args.get('chart', '')
    # Replace all whitespaces with the plus character
    # This is needed as base64 in request arguments, replaces these characters before
    chart = "+".join(chart.split())
    # The same happens in the ending of the base64 string, here a whitespace can be missing which has to be replaced
    # with a plus character
    if not chart.endswith('='):
        chart += "+"
    return render_template('chart.html', chart=chart)


def general_chart(filtered_scored: list, tables: list, xapi_base_uri: str) -> str:
    """
    Filters for tables and correct statements and calculates the percentage of correct assignments
    :param filtered_scored: list of xAPI statements
    :param tables: list of tables
    :param xapi_base_uri: xAPI base URI
    :return: correct assignment chart in percent (over all tables) base64 encoded
    """
    config = get_config()
    filtered_correct = filter_by_correct_score(filtered_scored)

    percentage_global = len(filtered_correct) / len(filtered_scored) * 100
    if percentage_global < 50:
        warnings.append({"type": "Problem", "message": "Unter 50 Prozent korrekte Zuordnungen."})

    percentage_values = [percentage_global]
    x_labels = ["Alle Tische"]

    if len(tables) > 1:
        for table in tables:
            x_labels.append("Tisch " + table)
            filtered_table = filter_by_table(statement_list=filtered_scored, table=table, xapi_base_uri=xapi_base_uri)
            filtered_correct = filter_by_correct_score(statement_list=filtered_table)
            percentage_value = len(filtered_correct) / len(filtered_table) * 100
            percentage_values.append(percentage_value)
            if percentage_value < 50:
                warnings.append(
                    {"type": "Problem", "message": "Unter 50 Prozent korrekte Zuordnungen bei Tisch " + table + "."})
    # Create bar plot with percentage
    percent_chart = pygal.Bar(value_formatter=lambda x: '{:.0f}%'.format(x), style=config.correct_style,
                              config=config.no_legend_config, range=(0, 100), max_scale=10)
    percent_chart.title = 'Korrekte Zuordnungen (in %)'
    percent_chart.x_labels = x_labels
    percent_chart.y_labels_major = [0]
    percent_chart.add('Prozent', percentage_values)
    return percent_chart.render_data_uri(width=900, height=250)


def time_frame_chart(filtered_scored: list, xapi_base_uri: str, tables: list) -> str:
    """
    Filters for time interval and tables and sum up the points in the time interval
    :param filtered_scored: list of xAPI statements
    :param tables: list of tables
    :param xapi_base_uri: xAPI base URI
    :return: points history chart (over all tables) base64 encoded
    """
    config = get_config()
    # Calculations for time frame
    step_millis = 5000
    interval_time = []
    points_dict = dict()
    for table in tables:
        points_dict[table] = []
    points_dict["all"] = []
    for timer_left in range(90000, 0, -step_millis):
        end_time_millis = config.max_timer_millis - timer_left + step_millis
        end_time_seconds = int(end_time_millis / 1000)
        interval_time.append(end_time_seconds)
        interval_filtered = filter_by_time_interval(statement_list=filtered_scored, xapi_base_uri=xapi_base_uri,
                                                    start_timer_left_in_millis=timer_left)
        if tables:
            for table in tables:
                filtered_table = filter_by_table(statement_list=interval_filtered, table=table,
                                                 xapi_base_uri=xapi_base_uri)
                filtered_correct = filter_by_correct_score(statement_list=filtered_table)
                filtered_false = filter_by_incorrect_score(statement_list=filtered_table)
                points = (len(filtered_correct) * 2) + (len(filtered_false) * -1)
                if not points_dict[table]:
                    points_dict[table].append(points)
                else:
                    before_points = points_dict[table][-1]
                    points_dict[table].append(before_points + points)
        else:
            filtered_correct = filter_by_correct_score(statement_list=interval_filtered)
            filtered_false = filter_by_incorrect_score(statement_list=interval_filtered)
            points = (len(filtered_correct) * 2) + (len(filtered_false) * -1)
            if not points_dict["all"]:
                points_dict["all"].append(points)
            else:
                before_points = points_dict["all"][-1]
                points_dict["all"].append(before_points + points)

    bar_chart = pygal.Line(style=config.table_style, x_title='Sekunden', y_title='Punkte')
    bar_chart.title = 'Punkteverlauf'
    bar_chart.x_labels = interval_time
    bar_chart.y_labels_major = [0]
    if tables:
        for table in tables:
            bar_chart.add("Tisch " + table, points_dict[table])
    else:
        bar_chart.add("", points_dict["all"])
    chart_time = bar_chart.render_data_uri(width=900, height=400)

    return chart_time


def update_statement_counting_dict(statement_list: list, tables_list: list, counting_dict: dict, counting_key: str,
                                   xapi_base_uri: str) -> dict:
    """
    Checks if statements are present and then counts the elements and adds it to the key (per table)
    :param statement_list: xAPI statement list
    :param tables_list: list of tables
    :param counting_dict: dictionary of counting
    :param counting_key: key to be counted
    :param xapi_base_uri: xAPI base URI
    :return: updated dictionary of counting
    """
    if len(statement_list) > 0:
        if len(tables_list) <= 1:
            counting_dict[counting_key] = len(statement_list)
        else:
            for table in tables_list:
                if counting_key not in counting_dict.keys():
                    # Create nested dictionary if it does not exist to not throw errors when writing nested object
                    counting_dict[counting_key] = {}
                counting_dict[counting_key][table] = len(
                    filter_by_table(statement_list=statement_list, table=table,
                                    xapi_base_uri=xapi_base_uri))
    return counting_dict


def add_data_points_to_chart_and_update_sum(tables: list, counting_dict: dict, chart, elem_count: int, max_value: int):
    """
    This adds data points to the chart and updates the sum of elements in the chart
    :param tables: list of tables
    :param counting_dict: counting dictionary
    :param chart: Pygal Chart
    :param elem_count: element to be updated
    :param max_value: current maximum value of data points
    :return: Pygal Chart, element count and maximum value
    """
    for table in tables:
        table_list = []
        for word in counting_dict.keys():
            table_list.append(counting_dict[word][table])
        chart.add('Tisch ' + table, table_list)
        if sum(table_list) > max_value - 1:
            max_value = sum(table_list) + 1
        elem_count += sum(table_list)
    return chart, elem_count, max_value


def false_regex_charts(regex_list: list, word_list: list, filtered_scored: list, xapi_base_uri: str,
                       tables: list) -> list:
    """
    Create charts with wrong elements per category
    :param regex_list: list of categories
    :param word_list: list of elements
    :param filtered_scored: list of xAPI statements
    :param xapi_base_uri: xAPI base URI
    :param tables: list of tables
    :return: list of charts as base64 of categories with wrong elements of these categories
    """
    config = get_config()
    max_value = 0
    charts_regex = []
    filtered_false = filter_by_incorrect_score(statement_list=filtered_scored)
    word_list = sorted(word_list)
    for regex in regex_list:
        word_counting_dict = {}
        filtered_regex = filter_by_category(statement_list=filtered_false, category=regex, xapi_base_uri=xapi_base_uri)
        if len(filtered_regex) > 0:
            for word in word_list:
                filtered_word = filter_by_element(statement_list=filtered_regex, element=word,
                                                  xapi_base_uri=xapi_base_uri)
                word_counting_dict = update_statement_counting_dict(statement_list=filtered_word, tables_list=tables,
                                                                    counting_key=word, counting_dict=word_counting_dict,
                                                                    xapi_base_uri=xapi_base_uri)
            bar_chart = pygal.StackedBar(style=config.table_style)
            bar_chart.title = 'Falsche Elemente für Kategorie ' + regex
            bar_chart.x_labels = word_counting_dict.keys()
            bar_chart.y_labels_major = [0]
            bar_chart.config.js[0] = config.server_url + "/static/js/pygal-custom-tooltips.js"
            elem_count = 0
            if len(tables) <= 1:
                bar_chart.add('Amount', word_counting_dict.values())
                elem_count = sum(word_counting_dict.values())
                bar_chart.config.show_legend = False
                max_word_value = max(word_counting_dict.values())
                if max_word_value > max_value - 1:
                    max_value = max_word_value + 1
            else:
                bar_chart, elem_count, max_value = add_data_points_to_chart_and_update_sum(tables=tables,
                                                                                           counting_dict=word_counting_dict,
                                                                                           chart=bar_chart,
                                                                                           elem_count=elem_count,
                                                                                           max_value=max_value)
            charts_regex.append({"chart": bar_chart, "count": elem_count})
    charts_regex = sorted(charts_regex, key=lambda chart: chart["count"], reverse=True)
    charts_regex = [set_ymax_and_create_chart(chart["chart"], max_value) for chart in charts_regex]
    return charts_regex


def false_words_charts(regex_list: list, word_list: list, filtered_scored: list, xapi_base_uri: str,
                       tables: list) -> list:
    """
    Create charts with wrong categories per element
    :param regex_list: list of categories
    :param word_list: list of elements
    :param filtered_scored: list of xAPI statements
    :param xapi_base_uri: xAPI base URI
    :param tables: list of tables
    :return: list of charts as base64 of elements with wrong categories of these elements
    """
    config = get_config()
    max_value = 0
    charts_word = []
    filtered_false = filter_by_incorrect_score(statement_list=filtered_scored)
    word_list = sorted(word_list)
    for word in word_list:
        category_counting_dict = {}
        filtered_word = filter_by_element(statement_list=filtered_false, element=word, xapi_base_uri=xapi_base_uri)
        if len(filtered_word) > 0:
            for regex in regex_list:
                filtered_regex = filter_by_category(statement_list=filtered_word, category=regex,
                                                    xapi_base_uri=xapi_base_uri)
                category_counting_dict = update_statement_counting_dict(statement_list=filtered_regex,
                                                                        tables_list=tables,
                                                                        counting_dict=category_counting_dict,
                                                                        counting_key=regex,
                                                                        xapi_base_uri=xapi_base_uri)
            bar_chart = pygal.StackedBar(style=config.table_style)
            bar_chart.title = 'Falsche Kategorien für Element ' + word
            bar_chart.x_labels = category_counting_dict.keys()
            bar_chart.y_labels_major = [0]
            elem_count = 0
            if len(tables) <= 1:
                bar_chart.add('Amount', category_counting_dict.values())
                bar_chart.config.show_legend = False
                max_category_value = max(category_counting_dict.values())
                if max_category_value > max_value - 1:
                    max_value = max_category_value + 1

                elem_count = sum(category_counting_dict.values())
            else:
                add_data_points_to_chart_and_update_sum(tables=tables, counting_dict=category_counting_dict,
                                                        chart=bar_chart, elem_count=elem_count, max_value=max_value)
            charts_word.append({"chart": bar_chart, "count": elem_count})
    charts_word = sorted(charts_word, key=lambda chart: chart["count"], reverse=True)
    charts_word = [set_ymax_and_create_chart(chart["chart"], max_value) for chart in charts_word]

    return charts_word


def set_ymax_and_create_chart(chart, max_value: int) -> str:
    """
    Set the range of y-labels of the graph
    :param chart:
    :param max_value:
    :return: base64 encoded chart
    """
    chart.config.y_labels = range(0, max_value + 1)
    if max_value > 10:
        chart.config.y_labels = range(0, max_value + 1, 2)
    return chart.render_data_uri(width=900, height=400)


def get_or_update_cache(start: str, end: str, xapi_base_uri: str):
    """
    Get the cache when parameters are unchanged or update the cache when parameters change
    :param start: start time as datetime string
    :param end: end time as datetime string
    :param xapi_base_uri: xAPI base URI
    :return: cached statements
    """
    if cache == {}:
        statements = get_statements(start, end)
        cache['start'] = start
        cache['end'] = end
        cache['uri'] = xapi_base_uri
        cache['statements'] = statements
        return statements
    elif cache['start'] != start or cache['end'] != end or cache['uri'] != xapi_base_uri:
        statements = get_statements(start, end)
        cache['start'] = start
        cache['end'] = end
        cache['uri'] = xapi_base_uri
        cache['statements'] = statements
        return statements
    else:
        return cache['statements']


def word_chart_relative(xapi_base_uri: str, filtered_scored: list, tables: list, word_list: list) -> str:
    """
    Create chart for correct assignments per element (only show below 100% accuracy)
    :param xapi_base_uri: xAPI base URI
    :param filtered_scored: list of xAPI statements
    :param tables: list of tables
    :param word_list: list of words
    :return: chart as base64 for correct assignments per element (only show below 100% accuracy)
    """
    config = get_config()
    percentage_chart_base_title = 'Korrekte Zuordnungen (in %; nur Elemente unter 100%)'
    percent_chart = pygal.HorizontalBar(value_formatter=lambda x: '{:.0f}%'.format(x), style=config.table_style)
    percent_chart.title = percentage_chart_base_title
    # Gather list of words to exclude
    excluding_list = []
    for word in word_list:
        filtered_word = filter_by_element(statement_list=filtered_scored, element=word, xapi_base_uri=xapi_base_uri)
        filtered_correct = filter_by_correct_score(statement_list=filtered_word)
        if len(filtered_correct) == len(filtered_word):
            excluding_list.append(word)
    current_word_list = sorted(filter_by_exclusion_list(list_element=word_list, exclusion_list=excluding_list),
                               reverse=True)
    percent_chart.x_labels = current_word_list
    percent_chart.y_labels_major = [0]
    # Start calculations
    for table in tables:
        filtered_table = filter_by_table(statement_list=filtered_scored, table=table, xapi_base_uri=xapi_base_uri)
        percentage_list = []
        for word in current_word_list:
            filtered_word = filter_by_element(statement_list=filtered_table, element=word, xapi_base_uri=xapi_base_uri)
            filtered_correct = filter_by_correct_score(statement_list=filtered_word)
            if len(filtered_word) == 0:
                percentage_list.append(0)
            else:
                percentage = len(filtered_correct) / len(filtered_word) * 100
                percentage_list.append(percentage)
                if percentage == 0:
                    warnings.append(
                        {"type": "Problem", "message": "Element " + word + " wurde nur falsch von Tisch " + table +
                                                       " zugeordnet.",
                         "img": "/static/img/" + word + ".png"})
        percent_chart.add('Tisch ' + table, percentage_list)
    percent_chart.config.js[0] = config.server_url + "/static/js/pygal-custom-tooltips.js"
    return percent_chart.render_data_uri(width=900, height=400)


def word_charts_absolute(xapi_base_uri: str, filtered_scored: list, tables: list, word_list: list) -> list:
    """
    List of charts per table and one for all tables that shows absolute amount of correctly and incorrectly assigned
    elements.
    :param xapi_base_uri: xAPI base URI
    :param filtered_scored: xAPI statement list
    :param tables: list of tables
    :param word_list: list of words
    :return: list of charts as base64 of correctly and incorrectly assigned elements per table
    """
    config = get_config()
    max_value = 0
    word_category_charts_absolute = []
    absolute_chart_base_title = 'Korrekte Zuordnungen (absolut)'
    # Gather list of words to exclude
    excluding_list = []
    for word in word_list:
        filtered_word = filter_by_element(statement_list=filtered_scored, element=word, xapi_base_uri=xapi_base_uri)
        if len(filtered_word) == 0:
            excluding_list.append(word)
    current_word_list = sorted(filter_by_exclusion_list(list_element=word_list, exclusion_list=excluding_list),
                               reverse=True)
    if len(tables) > 1:
        for table in tables:
            filtered_table = filter_by_table(statement_list=filtered_scored, table=table, xapi_base_uri=xapi_base_uri)
            absolute_chart_title = absolute_chart_base_title + ' Tisch ' + table

            correct_dict, incorrect_dict, max_value = get_correct_and_incorrect_per_element(
                statement_list=filtered_table, element_list=current_word_list,
                xapi_base_uri=xapi_base_uri, max_value=max_value)

            bar_chart = pygal.HorizontalStackedBar(style=config.correct_style)
            bar_chart.title = absolute_chart_title
            word_category_charts_absolute.append(
                update_chart_with_data_and_custom_js(chart=bar_chart, x_labels=current_word_list,
                                                     data={'Korrekt': correct_dict.values(),
                                                           'Inkorrekt': incorrect_dict.values()}))

    correct_dict, incorrect_dict, max_value = get_correct_and_incorrect_per_element(element_list=current_word_list,
                                                                                    statement_list=filtered_scored,
                                                                                    xapi_base_uri=xapi_base_uri,
                                                                                    max_value=max_value)
    bar_chart = pygal.HorizontalStackedBar(style=config.correct_style)
    bar_chart.title = absolute_chart_base_title + " Alle Tische"
    word_category_charts_absolute.append(
        update_chart_with_data_and_custom_js(chart=bar_chart, x_labels=current_word_list,
                                             data={'Korrekt': correct_dict.values(),
                                                   'Inkorrekt': incorrect_dict.values()}))

    word_category_charts_absolute = [set_ymax_and_create_chart(chart, max_value) for chart in
                                     word_category_charts_absolute]
    return word_category_charts_absolute


def get_correct_and_incorrect_per_element(element_list: list, statement_list: list, xapi_base_uri: str, max_value: int):
    """
    Get correct and incorrect statements per element as dictionary keys
    :param element_list: list of elements
    :param statement_list: list of xAPI statements
    :param xapi_base_uri: xAPI base URI
    :param max_value: maximum value as integer
    :return: correct and incorrect dictionary, maximum value
    """
    correct_dict = {}
    incorrect_dict = {}
    for word in element_list:
        filtered_word = filter_by_element(statement_list=statement_list, element=word, xapi_base_uri=xapi_base_uri)
        filtered_incorrect = filter_by_incorrect_score(statement_list=filtered_word)
        filtered_correct = filter_by_correct_score(statement_list=filtered_word)
        correct_dict[word] = len(filtered_correct)
        incorrect_dict[word] = len(filtered_incorrect)
        if max_value < len(filtered_word):
            max_value = len(filtered_word)
    return correct_dict, incorrect_dict, max_value


def update_chart_with_data_and_custom_js(chart, x_labels: list, data: dict):
    """
    Update a pygal chart with custom data and custom javascript tooltips
    :param chart: Pygal chart
    :param x_labels: list of labels for the x-axis
    :param data: dictionary of data, keys are dimensions, values are lists of elements for each x-axis label
    :return: Pygal Chart
    """
    config = get_config()
    chart.x_labels = x_labels
    chart.y_labels_major = [0]
    for key in data.keys():
        chart.add(key, data[key])
    chart.config.js[0] = config.server_url + "/static/js/pygal-custom-tooltips.js"
    return chart


def parse_sessions(request_args: flask.Request.args) -> list:
    """
    Get all sessions from request args.
    :param request_args: flask request args object
    :return: list of sessions
    """
    session_count_string = request_args.get('sessioncount', '')
    if session_count_string == '':
        return []
    session_count = int(session_count_string)
    sessions = []
    counter = 0
    for i in range(session_count):
        current_session = request_args.get('session' + str(i), '')
        if current_session != '':
            sessions.append(current_session)
        counter += 1
    return sessions


def get_session_ids(statements: list, xapi_base_uri: str) -> (list, str):
    """
    Get list of sessions with detailed information for the user to choose
    :param statements: list of xAPI statements
    :param xapi_base_uri: xAPI base URI
    :return: list of sessions and session count
    """
    sessions = []
    filtered_valid = filter_by_valid_session_id(statement_list=statements, xapi_base_uri=xapi_base_uri)
    filtered_started = filter_by_verb(statement_list=filtered_valid, verb='started')
    session_ids = set((elem['context']['extensions'][xapi_base_uri + 'sessionId'] for elem in filtered_started))
    for index, session_id in enumerate(session_ids):
        filtered_session = filter_by_session_id(statement_list=filtered_valid, session_id=session_id,
                                                xapi_base_uri=xapi_base_uri)
        timestamp = (datetime.datetime.strptime(filtered_session[0]['timestamp'],
                                                "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=1)).strftime(
            "%d.%m. %H:%M:%S Uhr")
        table = 'None'
        if xapi_base_uri + 'displayNbr' in filtered_session[0]['context']['extensions'].keys():
            table = filtered_session[0]['context']['extensions'][xapi_base_uri + 'displayNbr']
        if xapi_base_uri + 'level' in filtered_session[0]['context']['extensions'].keys():
            level = filtered_session[0]['context']['extensions'][xapi_base_uri + 'level']
        else:
            level = filtered_session[1]['context']['extensions'][xapi_base_uri + 'level']
        sessions.append({'name': 'session' + str(index), 'id': session_id, 'timestamp': timestamp,
                         'statementCount': str(len(filtered_session)), 'table': table, 'level': level})
    return sessions, str(len(sessions))


def update_general_infos(selected_sessions: list, statements: list, xapi_base_uri: str):
    """
    Update the general_infos element consisting of the categories, words and solutions for the given sessions
    :param selected_sessions: list of sessions
    :param statements: list of xAPI statements
    :param xapi_base_uri: xAPI base URI
    """
    config = get_config()
    dict_key = str(selected_sessions)
    if dict_key in general_infos:
        return
    general_infos[dict_key] = {}
    search_for = ["regEx", "words", "solution"]

    filtered_started = filter_by_verb(statement_list=statements, verb='started')
    tables_set = set()
    for elem in filtered_started:
        if xapi_base_uri + 'displayNbr' in elem['context']['extensions'].keys():
            table = elem['context']['extensions'][xapi_base_uri + 'displayNbr']
            tables_set.add(table)
    first_elem = filtered_started[0]
    xapi_extensions = first_elem['context']['extensions']
    for key in search_for:
        if xapi_base_uri + key in xapi_extensions.keys():
            general_infos[dict_key][key] = json.loads(xapi_extensions[xapi_base_uri + key])
        else:
            warnings.append({"type": "Warnung", "message": "Konfiguration konnte nicht gelesen werden. Geladene "
                                                           "Lösung könnte veraltet sein."})
            general_infos[dict_key][key] = config.fallback_game_config[xapi_base_uri][key]
    tables = list(tables_set)
    tables.sort(key=int)
    general_infos[dict_key]["tables"] = tables
    info_regex = general_infos[dict_key]["regEx"]
    general_infos[dict_key]["levels"] = list(info_regex.keys())
    regex_overwrite_elem = {}
    for level in info_regex.keys():
        regex_overwrite_elem[level] = [list(set(info_regex[level][0]))]
    general_infos[dict_key]["regEx"] = regex_overwrite_elem


def aggregate_all_words(levels: list, selected_sessions: list) -> list:
    """
    Aggregate all words from the general_infos object
    :param levels: list of levels
    :param selected_sessions: list of sessions
    :return: list of words
    """
    word_set = set()
    for level in levels:
        word_set.update(general_infos[str(selected_sessions)]['words'][level][0]['matching'])
        word_set.update(general_infos[str(selected_sessions)]['words'][level][0]['nonMatching'])
    return list(word_set)


def aggregate_all_regex(levels: list, selected_sessions: list) -> list:
    """
    Aggregate all categories from the general_infos object
    :param levels: list of levels
    :param selected_sessions: list of sessions
    :return: list of categories
    """
    regex_set = set()
    for level in levels:
        regex_set.update(general_infos[str(selected_sessions)]['regEx'][level][0])
    return list(regex_set)
