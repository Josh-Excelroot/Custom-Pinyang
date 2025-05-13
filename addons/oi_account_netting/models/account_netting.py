'''
Created on Oct 20, 2021

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, _
from odoo.exceptions import Warning

class AccountNetting(models.Model):
    _name = 'account.netting'
    _description = 'Account Netting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    _states = {'draft' : [('readonly', False)]}
    
    name = fields.Char('Number', compute = '_calc_name', store = True)
    journal_id = fields.Many2one('account.journal', required = True, readonly= True, states=_states, default = lambda self: self.env['account.move']._get_default_journal())
    move_id = fields.Many2one('account.move', string='Journal Entry', copy=False, readonly=True)
    
    company_id = fields.Many2one('res.company', required = True, default = lambda self: self.env.user.company_id, readonly= True, states=_states)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id, readonly= True, states=_states)
    
    receivable_partner_id = fields.Many2one('res.partner', required=True, domain = ['|', ('is_company','=', True), ('parent_id','=', False)], readonly= True, states=_states)
    payable_partner_id = fields.Many2one('res.partner', required=True, domain = ['|', ('is_company','=', True), ('parent_id','=', False)], readonly= True, states=_states)
    
    ref = fields.Char(string='Reference', copy=False, readonly= True, states=_states, default = "AR/AP netting")
    date = fields.Date(string='Date', required = True, default=fields.Date.today(), readonly= True, states=_states)
 
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
        ], string='Status', required=True, readonly=True, copy=False, track_visibility=True,
        default='draft', compute = '_calc_state', store = True)
    
    receivable_line_ids = fields.Many2many('account.move.line', string='Receivable Items', relation='account_netting_receivable_lines_rel', copy=False, readonly= True, states=_states)
    payable_line_ids = fields.Many2many('account.move.line', string='Payable Items', relation='account_netting_payable_lines_rel', copy=False, readonly= True, states=_states)
        
    receivable_balance = fields.Monetary(compute = '_calc_receivable_balance', store = True)
    payable_balance = fields.Monetary(compute = '_calc_payable_balance', store = True)
    
    balance = fields.Monetary(compute = '_calc_balance', store = True)
    balance_type = fields.Selection([("pay", "To pay"), ("receive", "To receive")], compute = '_calc_balance', store = True)
    
    payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid')],
        string='Payment', store=True, readonly=True, copy=False, track_visibility=True,
        compute='_calc_payment_state')
    
    amount_residual = fields.Monetary(compute = '_calc_amount_residual', store = True)
    
    payment_ids = fields.One2many('account.payment','account_netting_id')
    payment_count = fields.Integer(compute = '_calc_payment_count')
    
    @api.depends('payment_ids')
    def _calc_payment_count(self):
        for record in self:
            record.payment_count = len(record.payment_ids)
    
    @api.depends('move_id.name')
    def _calc_name(self):
        for record in self:
            record.name = record.move_id.name or '/'
            
    @api.depends('move_id.state')
    def _calc_state(self):
        for record in self:
            record.state = record.move_id.state or 'draft'            
    
    @api.onchange('receivable_partner_id')
    def _onchange_receivable_partner(self):
        self.payable_partner_id = self.receivable_partner_id.id
    
    def _compute_balance(self, line_ids):
        balance = 0
        for line in line_ids:            
            if line.amount_currency:
                balance += line.currency_id._convert(line.amount_residual_currency, self.currency_id, self.company_id, self.date)
            else:
                balance += line.company_currency_id._convert(line.amount_residual, self.currency_id, self.company_id, self.date)
        return self.currency_id.round(balance)
    
    @api.depends('receivable_line_ids')
    def _calc_receivable_balance(self):
        for record in self:
            record.receivable_balance = record._compute_balance(record.receivable_line_ids)
            
    @api.depends('payable_line_ids')
    def _calc_payable_balance(self):
        for record in self:
            record.payable_balance = record._compute_balance(record.payable_line_ids) * -1
    
    @api.depends('receivable_line_ids.amount_residual','receivable_line_ids.amount_residual_currency','payable_line_ids.amount_residual','payable_line_ids.amount_residual_currency')    
    def _calc_amount_residual(self):
        for record in self:
            amount_residual = record._compute_balance(record.receivable_line_ids + record.payable_line_ids)
            if record.balance_type == 'pay':
                amount_residual *=-1
            record.amount_residual = amount_residual
    
    @api.depends('receivable_balance','payable_balance')    
    def _calc_balance(self):
        for record in self:
            balance = record.receivable_balance - record.payable_balance
            record.balance_type = balance > 0 and 'receive' or 'pay'
            record.balance = abs(balance)
                
    @api.depends('move_id','amount_residual', 'balance', 'state')
    def _calc_payment_state(self):
        for record in self:
            if not record.move_id or record.state!='posted':
                record.payment_state = False
                continue
            
            if not record.amount_residual:
                record.payment_state = 'paid'
            elif record.amount_residual == record.balance:
                record.payment_state = 'not_paid'
            else:
                record.payment_state = 'partial'
                            
    def action_post(self):
        if not self.receivable_line_ids:
            raise Warning(_('Please select receivable items'))
        if not self.payable_line_ids:
            raise Warning(_('Please select payable items'))        
        
        move_vals = {
            'journal_id' : self.journal_id.id,
            'ref' : self.ref,
            'date' : self.date,
            'line_ids' : []
            }
        
        line_vals = []
        netting_amount = min(self.receivable_balance, self.payable_balance)
        
        available_amount = {
            'receivable' : netting_amount,
            'payable' : netting_amount,
            }
        
        def add_balance(account_id, balance, partner):
            if account_id.internal_type=='payable':
                balance = min(available_amount['payable'], -balance)
                available_amount['payable'] -= balance
                balance *=-1
            else:
                balance = min(available_amount['receivable'], balance)
                available_amount['receivable'] -= balance
            
            if not balance:
                return
            
            vals = {
                'account_id' : account_id.id,
                'partner_id' : partner.id,
                'amount_currency' : 0,
                }
            if self.currency_id != self.company_id.currency_id:
                vals.update({
                    'currency_id' : self.currency_id.id,
                    'amount_currency' : -balance,
                    'credit' : self.currency_id._convert(balance, self.company_id.currency_id, self.company_id, self.date),
                    'debit' : 0
                    })
            else:
                vals.update({
                    'credit' : balance,
                    'debit' : 0
                    })
            if vals['credit'] < 0:
                vals.update({
                    'debit' : abs(vals['credit']),
                    'credit' : 0
                    })
            
            for old_vals in line_vals:
                if old_vals['account_id'] == vals['account_id']:
                    for name in ['amount_currency','debit','credit']:
                        old_vals[name] += vals[name] 
                    vals = False
                    break
            
            if vals:
                line_vals.append(vals)            
        
        line_ids = (self.receivable_line_ids + self.payable_line_ids).sorted(key = lambda line: (line.date_maturity or line.date, line.id))
        
        for line in line_ids:
            balance = self._compute_balance(line)
            add_balance(line.account_id, balance, line.partner_id)            
        
        for vals in line_vals:
            move_vals['line_ids'].append((0,0, vals))
        
        if self.move_id and self.move_id.journal_id != self.journal_id:
            self.move_id = False
                    
        if self.move_id:
            move_vals['line_ids'].insert(0, (5,))
            self.move_id.write(move_vals)
        else:
            self.move_id = self.env['account.move'].create(move_vals)        
        
        self.move_id.action_post()
        
        for line in line_ids:
            move_line = self.move_id.line_ids.filtered(lambda move_line: move_line.account_id == line.account_id)
            if not move_line.reconciled:
                (move_line + line).reconcile()        
        
    def button_cancel(self):
        if self.move_id:
            self.move_id.button_cancel()

    def unlink(self):
        self.mapped('move_id').unlink()
        return super(AccountNetting, self).unlink()
    
    def _get_payment_context(self):
        print('>>>>>>>>>>>>>  _get_payment_context default_amount=', self.amount_residual)
        print('>>>>>>>>>>>>>  _get_payment_context default_communication=', self.ref)
        context = {
            'active_ids' : self.ids,
            'active_model' : self._name,
            'active_id' : self.id,
            'default_amount' : self.amount_residual,
            'default_currency_id' : self.currency_id.id,
            'default_communication' : self.ref,
            'default_account_netting_id' : self.id            
            }        
        
        if self.balance_type == 'pay' :
            context.update({
                'default_partner_id' : self.payable_partner_id.id,
                'default_payment_type' : self.amount_residual > 0 and 'outbound' or 'inbound',
                'default_partner_type' : 'supplier',
                })
        else:
            context.update({
                'default_partner_id' : self.receivable_partner_id.id,
                'default_payment_type' : self.amount_residual > 0 and 'inbound' or 'outbound',
                'default_partner_type' : 'customer',
                })
        return context        
    
    def action_register_payment(self):
        return {
            'type' : 'ir.actions.act_window',
            'target' : 'new',
            'res_model' : 'account.payment',
            'view_mode': 'form',
            'view_id' : self.env.ref("oi_account_netting.view_account_payment_account_netting_form").id,
            'context' : self._get_payment_context()                
            }
    
    
    def action_view_payments(self):
        action, = self.env.ref("account.action_account_payments").read([])
        action.update({
            'context' : self._get_payment_context(),
            'domain' : [('account_netting_id','=', self.id)]
            })
        if len(self.payment_ids) == 1:
            action.update({
                'views' : [(False, 'form')],
                'res_id' : self.payment_ids.id
                })
        return action