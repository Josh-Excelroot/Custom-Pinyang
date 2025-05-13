from odoo import api, exceptions, fields, models, _

class AccountInvoice(models.Model):

    _inherit = 'hr.expense'

    ocr_ready_to_execute = fields.Boolean('OCR Ready to Execute')
    ocr_completed = fields.Boolean('OCR Completed')

    @api.multi
    def action_get_attachment(self):
        attachments = self.env['ir.attachment'].search([
            ('active', '=', True),
            ('res_model', '=', 'account.invoice'),
            ('res_id', '=', self.id)
        ])
        for i in attachments:
            print(i)
            filename = i.name
            pdf_attachment = i.datas
            if self.partner_id.id:
                partner = self.partner_id
            else:
                partner = False
            self.read_invoice(pdf_attachment, partner, self)
