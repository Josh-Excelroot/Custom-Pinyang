# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "All in one Sticky",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",    
    "category": "Extra Tools",
    "summary": "Set Fix Header Module, Form View Freeze Header, Set Permanent Header, Website Sticky Header, Freeze form view status bar,Sticky list view header,Fix list view footer,Sticky chatter header,Freeze list view inside form view Odoo",
    "description": """This module provides a sticky form view status bar, sticky list view header, sticky list view footer, sticky chatter header & sticky list view inside form view.""",    
    "version":"12.0.6",
    "depends" : [
                
                "base",
                "base_setup"
            ],
    "application" : True,
    "data" : [
       
         "views/res_config_view.xml",
         "form_sticky/views/form_assets_backend.xml",
         "list_sticky/views/list_assets_backend.xml", 
         "list_inside_form_sticky/views/list_inside_form_assets_backend.xml", 
         "pivot_sticky/views/pivot_assets_backend.xml",
         "chatter_sticky/views/chatter_assets_backend.xml"    
            ],      
               
    "images": ['static/description/background.png',],  
    "auto_install":False,
    "installable" : True,
    "price": 25,
    "currency": "EUR"   
}
