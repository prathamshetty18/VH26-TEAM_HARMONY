import requests

base_url = 'http://127.0.0.1:8000'
test_cases = [
    {'message': 'show diagram', 'machine_filter': 'Hydraulic Press'},
    {'message': 'diagram', 'machine_filter': 'Hydraulic Press'},
    {'message': 'show schematic', 'machine_filter': 'Press-200'},
    {'message': 'What does E101 mean?', 'machine_filter': 'Hydraulic Press'},
    {'message': 'What does E101 mean?', 'machine_filter': 'Press-200'},
    {'message': 'show diagram for robotarm-300', 'machine_filter': None},
    {'message': 'show diagram for cnc-100', 'machine_filter': None},
]

for tc in test_cases:
    r = requests.post(f'{base_url}/query', json=tc).json()
    diags = [d.get('filename') for d in r.get('diagrams', [])]
    ans = (r.get('answer') or '')[:60].replace('\n', ' ')
    print(f"Msg: {tc['message']} (filter: {tc['machine_filter']})")
    print(f"   Ans: {ans} | Diags: {diags} | Sources: {len(r.get('sources', []))}")
