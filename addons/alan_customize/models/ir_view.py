# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models
from lxml import etree, html
from odoo import api, fields, models
TIMELINE_VIEW = ('timeline', 'Timeline')

#kashif 19march 24: changes regarding css not being saved in website
class IrUIView(models.Model):
    _inherit = 'ir.ui.view'

    @api.multi
    def save(self, value, xpath=None):
        """ Update a view section. The view section may embed fields to write

        Note that `self` record might not exist when saving an embed field

        :param str xpath: valid xpath to the tag to replace
        """
        self.ensure_one()

        arch_section = html.fromstring(
            value, parser=html.HTMLParser(encoding='utf-8'))

        if xpath is None:
            # value is an embedded field on its own, not a view section
            self.save_embedded_field(arch_section)
            return

        for el in self.extract_embedded_fields(arch_section):
            self.save_embedded_field(el)

            # transform embedded field back to t-field
            el.getparent().replace(el, self.to_field_ref(el))

        for el in self.extract_oe_structures(arch_section):
            if self.save_oe_structure(el):
                # empty oe_structure in parent view
                empty = self.to_empty_oe_structure(el)
                if el == arch_section:
                    arch_section = empty
                else:
                    el.getparent().replace(el, empty)

        new_arch = self.replace_arch_section(xpath, arch_section)
        old_arch = etree.fromstring(self.arch.encode('utf-8'))
        if not self._are_archs_equal(old_arch, new_arch):
            self._set_noupdate()
            self.write({'arch': self._pretty_arch(new_arch)})
            self.update_auctual_view_arch(arch_section, new_arch)

    def update_auctual_view_arch(self,arch,new_arch):
        count=0
        for elem in arch.getchildren():
            collection = False
            if 'data-collection_id' in elem.attrib:
                collection = self.env['multitab.configure'].browse(
                    int(elem.attrib.get('data-collection_id')))
            if collection and elem.attrib.get('data-snippet_type') == 'single':
                if (elem).xpath("//div[hasclass('seaction-head')]"):
                    collection.inner_html = self._pretty_arch((elem).xpath("//div[hasclass('seaction-head')]")[count])
            else:
                if 'data-collection_id' in elem.attrib:
                    collection = self.env['collection.configure'].browse(
                        int(elem.attrib.get('data-collection_id')))
                    if collection:
                        if (elem).xpath("//div[hasclass('seaction-head')]"):
                            collection.inner_html = self._pretty_arch(
                                (elem).xpath("//div[hasclass('seaction-head')]")[count])


            count+=1