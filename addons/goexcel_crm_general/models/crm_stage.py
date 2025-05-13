from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    stay_check_type = fields.Selection([('none', 'None'), ('time', 'Time of next day'), ('duration', 'Duration')],
                                       default='none', required=True,
                                       help='Alert user and change color to red when lead\'s stage stay time/duration '
                                            'pass the condition')
    stay_check_time = fields.Float(help='Alert on selected time after next day of following stage changed time')
    stay_check_duration = fields.Float(help='Alert on selected duration pass from following stage changed time')

    def write(self, vals):
        if vals.get('stay_check_time', False) and vals['stay_check_time'] >= 24:
            raise UserError('Invalid Time! (Must be between 00:00 - 23:59')
        return super(CrmStage, self).write(vals)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    def _login(cls, db, login, password):
        result = super(ResUsers, cls)._login(db, login, password)
        with cls.pool.cursor() as cr:
            self = api.Environment(cr, SUPERUSER_ID, {})
            user = self[cls._name].search(self[cls._name]._get_login_domain(login))
            # get expired stage leads having salesperson same as logged in user
            expired_stage_leads = self['crm.lead'].get_expired_stage_leads().filtered(lambda l: l.user_id == user)
            print(user.name,'>>>>>>>> esl:',expired_stage_leads)
            for lead in expired_stage_leads:
                print('>>>>>>>> l:',lead)
                # user.notify_danger(message=f'Dear {user.name}, please act on the expired {lead.name} at the {lead.stage_id.name}')
        return result


