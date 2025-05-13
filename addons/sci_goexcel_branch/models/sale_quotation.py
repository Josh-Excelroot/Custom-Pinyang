from odoo import api, fields, models,exceptions


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    branch = fields.Many2one('account.analytic.tag', string='Branch')

    @api.model
    def create(self, vals):
        sequence = ''
        if vals.get('branch'):  #if user select branch manually
            sequence = self.env['ir.sequence'].search([
                ('code', '=', 'sale.order'),
                ('branch', '=', vals.get('branch')),
            ], limit=1)
        elif self.env.user.default_branch.id:  #if user didnt select branch
            vals['branch'] = self.env.user.default_branch.id
            sequence = self.env['ir.sequence'].search([
                ('code', '=', 'sale.order'),('branch', '=', self.env.user.default_branch.id),
            ], limit=1)

        else:  #for portal which submitted by the customer, branch is empty
            if vals.get('partner_id'):
                partner = self.env['res.partner'].browse(vals.get('partner_id'))

                if partner and partner.branch_ids:

                    # branch_id = False

                    # for branch in partner.branch_ids.ids:
                    #     branch_id = branch
                    #     break
                    # print('branch id=',branch_id)
                    sequence = self.env['ir.sequence'].search([
                        ('code', '=', 'sale.order'),
                        ('branch', '=', partner.category_id.id),
                    ], limit=1)
                    print("seq",sequence)

                    branch_id = partner.branch_ids.ids[0]
                    branch = self.env['account.analytic.tag'].search([('id', '=', branch_id)], limit=1)
                    vals['branch'] = branch[0].id

            #get the customer default branch

        #print('>>>>>>> sci_goexcel_branch SO create default_branch=', self.env.user.default_branch.id)
        # if not sequence:
        #     sequence = self.env['ir.sequence'].create({
        #         'code': 'sale.order',
        #         'branch': self.env.user.default_branch.id,
        #     })
        res = super(SaleQuotation, self).create(vals)
        if sequence:
            res.name = sequence._next()
        return res

