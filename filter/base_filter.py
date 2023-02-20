def filter_by_correct_score(statement_list: list, correct_score=2) -> list:
    return list(filter(lambda elem: elem['result']['score']['raw'] == correct_score, statement_list))


def filter_by_incorrect_score(statement_list: list, incorrect_score=-1) -> list:
    return list(filter(lambda elem: elem['result']['score']['raw'] == incorrect_score, statement_list))


def filter_by_table(statement_list: list, table: str, xapi_base_uri: str) -> list:
    return list(
        filter(lambda elem: elem['context']['extensions'][xapi_base_uri + 'displayNbr'] == table,
               statement_list))


def filter_by_time_interval(statement_list: list, start_timer_left_in_millis: int, xapi_base_uri: str,
                            interval_in_millis=5000) -> list:
    return list(
        filter(lambda elem: int(
            elem['context']['extensions'][xapi_base_uri + 'timeleft']) < start_timer_left_in_millis and int(
            elem['context']['extensions'][
                xapi_base_uri + 'timeleft']) >= start_timer_left_in_millis - interval_in_millis, statement_list))


def filter_by_session_list(statement_list: list, session_list: list, xapi_base_uri: str) -> list:
    return list(
        filter(lambda elem: elem['context']['extensions'][xapi_base_uri + 'sessionId'] in session_list,
               statement_list))


def filter_by_category(statement_list: list, category: str, xapi_base_uri: str) -> list:
    return list(
        filter(lambda elem: elem['context']['extensions'][xapi_base_uri + 'regex'] == category, statement_list))


def filter_by_element(statement_list: list, element: str, xapi_base_uri: str) -> list:
    return list(
        filter(lambda elem: elem['context']['extensions'][xapi_base_uri + 'word'] == element, statement_list))


def filter_by_exclusion_list(list_element: list, exclusion_list: list) -> list:
    return [elem for elem in list_element if elem not in exclusion_list]


def filter_by_verb(statement_list: list, verb: str) -> list:
    return list(
        filter(lambda elem: elem['verb']['id'] == 'http://adlnet.gov/expapi/verbs/' + verb, statement_list))


def filter_by_session_id(statement_list: list, session_id: str, xapi_base_uri: str) -> list:
    return list(
        filter(lambda elem: elem['context']['extensions'][xapi_base_uri + 'sessionId'] == session_id,
               statement_list))


def filter_by_valid_session_id(statement_list: list, xapi_base_uri: str) -> list:
    return list(
        filter(lambda elem: xapi_base_uri + 'sessionId' in elem['context']['extensions'].keys(), statement_list))
