from odoo import api, models, fields, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError

from lxml import etree
import json
import ast


        #kashif 4oct23 .. added code to restrict DSR to edit states
class ResCountrys(models.Model):
    _inherit = 'res.country'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResCountrys, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            user = self.env.user
            user_is_crm_sale_person = user.has_group('goexcel_bps_security.crm_group_user')
            if  user_is_crm_sale_person and not user._is_admin():
                doc = etree.XML(res['arch'])
                # kashif 4july23: readonly status field for non accounting users
                state_field = doc.xpath("//field[@name='state_ids']")
                if state_field:
                    state_field = state_field[0]
                    state_field.set('readonly', '1')
                    modifiers = json.loads(state_field.get("modifiers"))
                    modifiers['readonly'] = True
                    state_field.set("modifiers", json.dumps(modifiers))
                # end
                res['arch'] = etree.tostring(doc)
        return res

#end