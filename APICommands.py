# ARM dev server
API_URI = 'https://apicued2019.xenplate.com/internalapi'
API_KEY = 'hqQuiDT6rdh3dRJpEKXTXfunjMZCN5vG'
_cert = None
test_patient_username = 'TestPatient'
test_patient_password = 'Escape78BrightLight'
test_plate_template_name = 'Raw Medical'
# test_plate_template_name = 'Key Plate'

_user_api_key = API_KEY
_key_plate_template_id = None
_key_plate_data_id = None
_record_id = None
_user_id = None
LONG_TIME_EPOCH: datetime = datetime(1800, 1, 1)


def get_api_key_header(api_key):
    return {'Authorization': f'X-API-KEY {api_key}'}


def from_long_time(long_date_time: int) -> datetime:
    return LONG_TIME_EPOCH + timedelta(seconds=long_date_time)


def to_long_time(date_time: datetime) -> int:
    return int((date_time - LONG_TIME_EPOCH).total_seconds())


def print_status(resp) -> bool:
    if resp.status_code == 200: return False

    print(f"{inspect.stack()[1][0].f_code.co_name}  Status={resp.status_code}  Reason={resp.reason}")

    return True


def record_search(patient_ID):
    filters = [
        {'operator': 1, 'property': 'IdNumber', 'value': patient_ID}
    ]

    resp = requests.post(f'{API_URI}/record/search',
                         json={'filters': filters},
                         headers=get_api_key_header(API_KEY),
                         cert=_cert)

    if print_status(resp): return

    response_json = resp.json()

    # pprint(response_json)
    return response_json['RecordSearchResult']['records'][0]['id']


def data_create(record_id, template_id, control_values: list):
    payload = {'record_id': record_id,
               'plate_template_id': template_id,
               'control_values': control_values}

    resp = requests.post(f'{API_URI}/data/create',
                         json={'data': payload, 'ignore_conflicts': True},
                         headers=get_api_key_header(_user_api_key),
                         cert=_cert)

    if print_status(resp): return

    response_json = resp.json()

    status = response_json['PlateDataCreateResult']['status']

    print(f"data_create Status={status}")

    if status != 0:
        pprint(response_json['PlateDataCreateResult'], width=120)

def template_read_active_full(plate_template_name):
    resp = requests.get(f'{API_URI}/template/read/active/full?plate_name={plate_template_name}',
                        headers=get_api_key_header(_user_api_key),
                        cert=_cert)
    
    if print_status(resp): return

    response_json = resp.json()

    status = response_json['PlateTemplateReadActiveByIdNameResult']['status']

    if status != 0: 
        print(f"Failed, status={status}")
        return

    return response_json['PlateTemplateReadActiveByIdNameResult']['plate_template']['id']

# END