# -*- coding: utf-8 -*-
{
    "name": "Sticky Notes",
    "version": "12.0.1.0.2",
    "category": "Productivity",
    "author": "faOtools",
    "website": "https://faotools.com/apps/12.0/sticky-notes-364",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "web"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/view.xml",
        "views/sticky_note.xml",
        "data/data.xml"
    ],
    "qweb": [
        "static/src/xml/*.xml"
    ],
    "js": [
        
    ],
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The tool to pin sticky indicative notes to any Odoo form view",
    "description": """
For the full details look at static/description/index.html

* Features * 
- Stickers to any documents
- Catchy reminders
- Private or shared



#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "28.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=93&ticket_version=12.0&url_type_id=3",
}