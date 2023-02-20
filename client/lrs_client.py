import requests


def get_statements(start, end):
    statement_list = []
    base_url = 'https://lrs.elearn.rwth-aachen.de'
    url = base_url + '/data/xAPI/statements?since=' + start + '&ascending=true&until=' + end
    headers = {'Authorization': 'Basic '
                                'ZTgyZDQ3ZmQ1NjU4Mzg5MTYyMDJjNjQ4NTJhMTRkZTFlYzBjYjkwYTowN2JkMTNhMjZiZTQ4YTIwZjY1ODg1NzFhYjNkYjRhNTNlNTgwMzg4',
               'Content-Type': 'application/json',
               'X-Experience-API-Version': '1.0.1'}
    response = requests.get(url=url, headers=headers)
    if response.status_code == 502:
        return []
    response_json = response.json()
    statements = response_json['statements']
    statement_list.extend(statements)
    while response_json['more'] != '':
        response = requests.get(url=base_url + response_json['more'], headers=headers)
        response_json = response.json()
        statement_list.extend(response_json['statements'])
    return statement_list
