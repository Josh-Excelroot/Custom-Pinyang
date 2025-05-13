from odoo import models, fields, api


class UnblockCreditRequest(models.TransientModel):
    _name = "unblock.credit.request.wiz"
    _description = "Unblock Overdue Partner"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    remark = fields.Text(string="Remark", default="For Overdue Unblock")


    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        #print('>>>>>>>>>>>> UnblockCreditRequest default_get=', str(self.sale_order_id.id))
        so_id = self.env['sale.order'].browse(self.env.context.get('so_id'))
        #print('>>>>>>>>>>>> UnblockCreditRequest default_get so_id=', str(self.env.context.get('so_id')))
        #so_id = self.env.context.get('active_id')
        #so = self.env['sale.order'].browse(self.env.context.get('sale_order_id'))
        #if so:
        rec.update({
            'remark': so_id.approval_reasons,
            'sale_order_id': so_id.id,
        })
        return rec


    @api.multi
    def action_make_request(self):
        if self.sale_order_id and self.sale_order_id.partner_id:
            data = {
                'partner_id': self.sale_order_id.partner_id.id,
                'current_is_overdue_block': self.sale_order_id.partner_id.is_overdue_block,
                'unblock_is_overdue_block': False,
                'requested_by_id': self.env.uid,
                'remark': self.remark,
                'order_id': self.sale_order_id.id,
            }
            self.env['partner.credit.approval'].create(data)
            self.sale_order_id.write({
                'state': 'approve',
            })
            self.sale_order_id.message_post(body=self.remark)


    @api.multi
    def action_cancel(self):
        so_id = self.env['sale.order'].browse(self.env.context.get('so_id'))
        so_id.write({
            'state': 'draft',
        })
