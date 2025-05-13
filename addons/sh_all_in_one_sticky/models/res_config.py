# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    enable_form_view_status_bar = fields.Boolean("Enable Form View Status Bar",default=False)
    enable_list_view_status_bar = fields.Boolean("Enable List View header",default=False)
    enable_list_footer_view_status_bar = fields.Boolean("Enable List Footer View",default=False)
    enable_list_inside_form_view = fields.Boolean("Enable List inside Form View ",default=False)
    enable_pivot_header_view = fields.Boolean("Enable Pivot Header View ",default=False)
    enable_chatter_header_view = fields.Boolean("Enable Chatter Header View",default=False)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    enable_form_view_status_bar = fields.Boolean("Enable Form View Status Bar",
                                             related='company_id.enable_form_view_status_bar',readonly=False)
    enable_list_view_status_bar = fields.Boolean("Enable List View header",
                                             related='company_id.enable_list_view_status_bar',readonly=False)
    enable_list_footer_view_status_bar = fields.Boolean("Enable List Footer View",
                                             related='company_id.enable_list_footer_view_status_bar',readonly=False)
    enable_list_inside_form_view = fields.Boolean("Enable List inside Form View ",
                                             related='company_id.enable_list_inside_form_view',readonly=False)
    enable_pivot_header_view = fields.Boolean("Enable Pivot Header View ",readonly=False,
                                              related='company_id.enable_pivot_header_view')
    enable_chatter_header_view = fields.Boolean("Enable Chatter Header View",readonly=False,
                                                related='company_id.enable_chatter_header_view')
    
    
    @api.onchange('enable_form_view_status_bar','enable_list_view_status_bar','enable_list_footer_view_status_bar','enable_list_inside_form_view',
                  'enable_pivot_header_view','enable_chatter_header_view')
    def _onchange_setting(self):
        is_enterprise = self.env['ir.module.module'].sudo().search([('name','=','web_enterprise')],limit=1)
        if is_enterprise:
            if self.env.ref('sh_all_in_one_sticky.form_enterprise_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.form_enterprise_assets_backend').write({'active':True})
                
            if self.enable_chatter_header_view:
                if self.env.ref('sh_all_in_one_sticky.form_chatter_enterprise_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.form_chatter_enterprise_assets_backend').write({'active':True})
            else:
                if self.env.ref('sh_all_in_one_sticky.form_chatter_enterprise_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.form_chatter_enterprise_assets_backend').write({'active':False})
        else:
            if self.env.ref('sh_all_in_one_sticky.form_enterprise_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.form_enterprise_assets_backend').write({'active':False})   
            if self.env.ref('sh_all_in_one_sticky.form_chatter_enterprise_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.form_chatter_enterprise_assets_backend').write({'active':False})     

    
    @api.onchange('enable_form_view_status_bar')
    def _onchange_enable_form_view_status_bar(self):
        if self.enable_form_view_status_bar:
            if self.enable_chatter_header_view:
                if self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend').write({'active':True})
                if self.env.ref('sh_all_in_one_sticky.chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.chatter_assets_backend').write({'active':False})
                    
            if self.env.ref('sh_all_in_one_sticky.form_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.form_assets_backend').write({'active':True})
        else:
            if self.enable_chatter_header_view:
                if self.env.ref('sh_all_in_one_sticky.chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.chatter_assets_backend').write({'active':True})
                if self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend').write({'active':False})
            if self.env.ref('sh_all_in_one_sticky.form_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.form_assets_backend').write({'active':False})
                
    @api.onchange('enable_list_view_status_bar')
    def _onchange_enable_list_view_status_bar(self):
        if self.enable_list_view_status_bar:
            if self.env.ref('sh_all_in_one_sticky.list_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.list_assets_backend').write({'active':True})
        else:
            self.enable_list_footer_view_status_bar = False
            if self.env.ref('sh_all_in_one_sticky.list_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.list_assets_backend').write({'active':False})
                
                
    @api.onchange('enable_list_footer_view_status_bar')
    def _onchange_enable_list_footer_view_status_bar(self):
        if self.enable_list_footer_view_status_bar and self.enable_list_view_status_bar:
            if self.env.ref('sh_all_in_one_sticky.list_footer_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.list_footer_assets_backend').write({'active':True})
        else:
            if self.env.ref('sh_all_in_one_sticky.list_footer_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.list_footer_assets_backend').write({'active':False})
                
                
    @api.onchange('enable_list_inside_form_view')
    def _onchange_enable_list_inside_form_view(self):
        if self.enable_list_inside_form_view:
            if self.env.ref('sh_all_in_one_sticky.list_inside_form_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.list_inside_form_assets_backend').write({'active':True})
        else:
            if self.env.ref('sh_all_in_one_sticky.list_inside_form_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.list_inside_form_assets_backend').write({'active':False})
                
                
    @api.onchange('enable_pivot_header_view')
    def _onchange_enable_pivot_view_status_bar(self):
        if self.enable_pivot_header_view:
            if self.env.ref('sh_all_in_one_sticky.pivot_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.pivot_assets_backend').write({'active':True})
        else:
            if self.env.ref('sh_all_in_one_sticky.pivot_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.pivot_assets_backend').write({'active':False})
                
    @api.onchange('enable_chatter_header_view')
    def _onchange_enable_chatter_header_view(self):
        if self.enable_chatter_header_view:
            if self.enable_form_view_status_bar:
                if self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend').write({'active':True})
                if self.env.ref('sh_all_in_one_sticky.chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.chatter_assets_backend').write({'active':False}) 
            else:
                if self.env.ref('sh_all_in_one_sticky.chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.chatter_assets_backend').write({'active':True})
                if self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend').write({'active':False})
        else:
            if self.env.ref('sh_all_in_one_sticky.chatter_assets_backend'):
                self.env.ref('sh_all_in_one_sticky.chatter_assets_backend').write({'active':False})
            if self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend'):
                    self.env.ref('sh_all_in_one_sticky.form_chatter_assets_backend').write({'active':False})