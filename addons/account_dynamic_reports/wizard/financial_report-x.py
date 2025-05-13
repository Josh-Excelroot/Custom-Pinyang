from datetime import datetime

data = {'report_lines': [
    {'name': 'PROFIT AND LOSS', 'self_id': 1, 'parent': 0, 'has_children': False, 'has_grand_children': False,
     'display_detail_temp': 'no_detail'},
    {'name': 'SALES', 'self_id': 2, 'parent': 0, 'has_children': True, 'has_grand_children': True,
     'display_detail_temp': 'no_detail'},
    {'name': '510-0000 SHIPPING LINE (MLO) - EXPORT', 'self_id': 30, 'parent': 2, 'has_children': True,
     'has_grand_children': False, 'display_detail_temp': 'no_detail'},
    {'name': '510-A001 AMS AMENMENT FEES', 'self_id': 'a', 'parent': 30, 'has_children': False,
     'has_grand_children': False, 'display_detail_temp': 'no_detail'},
    {'name': 'COG', 'self_id': 3, 'parent': 0, 'has_children': True, 'has_grand_children': True,
     'display_detail_temp': 'no_detail'},
    {'name': '610-0000 SHIPPING LINE (MLO) - EXPORT', 'self_id': 34, 'parent': 3, 'has_children': True,
     'has_grand_children': False, 'display_detail_temp': 'detail'},
    {'name': '510-A001 AMS AMENMENT FEES', 'self_id': 'a', 'parent': 34, 'has_children': False,
     'has_grand_children': False, 'display_detail_temp': 'no_detail'}
]}

hide_children = filter(lambda x:
                       x['display_detail_temp'] == 'no_detail' and
                       not x['has_grand_children'] and
                       x['has_children'],
                       data['report_lines'])
self_ids_to_hide_children = list(map(lambda x: x['self_id'], hide_children))
for idx, line in enumerate(data['report_lines']):
    if line['parent'] in self_ids_to_hide_children:
        data['report_lines'][idx]['hide'] = True
    else:
        data['report_lines'][idx]['hide'] = False

n = [{'name': line['name'], 'hide': line['hide'], 'self_id': line['self_id'], 'parent': line['parent'],
      'hc': line['has_children'], 'hgc': line['has_grand_children']} for line in data['report_lines']]
a = 1
