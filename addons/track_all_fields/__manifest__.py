# -*- coding: utf-8 -*-
{
    'name': "Track all fields",
    'version': '1.0.0',
    'license': 'LGPL-3',
    'category': 'Mail',
    'description': """
 It will track all the fields in mail chatter box for seleted models.

 How to use?
 1. Go to models views (Settings > Data Structure > Models)
 2. click on model and enable "Track all fields".

    """,
    'author': "Laxicon Solution",
    'depends': ['mail'],
    'data': [
        'views/views.xml',
    ],
}
