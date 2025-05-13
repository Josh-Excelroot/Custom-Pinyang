# -*- coding: utf-8 -*-

from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, body='', subject=None,
                     message_type='notification', subtype=None,
                     parent_id=False, attachments=None,
                     notif_layout=False, add_sign=True, model_description=False,
                     mail_auto_delete=True, **kwargs):
        context = self._context.copy()
        if self._context.get('from_composer', False):
            context.update({
                'mail_post_autofollow': False,
                'mail_create_nosubscribe': True,
            })
        return super(MailThread, self.with_context(context)).message_post(body=body, subject=subject,
                                                                          message_type=message_type, subtype=subtype,
                                                                          parent_id=parent_id, attachments=attachments,
                                                                          notif_layout=notif_layout, add_sign=add_sign, model_description=model_description,
                                                                          mail_auto_delete=mail_auto_delete, **kwargs)

    @api.multi
    def message_get_suggested_recipients(self):
        """ Returns suggested recipients for ids. Those are a list of
        tuple (partner_id, partner_name, reason), to be managed by Chatter. """

        model = self.env.context.get('thread_model', False) if self._name == 'mail.thread' else self._name
        if model and model != self._name and hasattr(self.env[model], 'message_post'):
            del self.env.context['thread_model']
            return self.env[model].message_get_suggested_recipients()

        result = dict((res_id, []) for res_id in self.ids)
        if 'user_id' in self._fields:
            for obj in self.sudo():  # SUPERUSER because of a read on res.users that would crash otherwise
                if not obj.user_id or not obj.user_id.partner_id:
                    continue
                obj._message_add_suggested_recipient(
                    result,
                    partner=obj.user_id.partner_id,
                    reason=self._fields['user_id'].string,
                )

        if 'partner_id' in self._fields:
            for obj in self.sudo():  # SUPERUSER because of a read on res.users that would crash otherwise
                if obj.partner_id:
                    self._message_add_suggested_recipient(
                        result,
                        partner=obj.partner_id,
                        reason=self._fields['partner_id'].string,
                    )

        return result


    @api.model
    def create(self, vals):
        return super(MailThread, self.with_context(mail_create_nosubscribe=1,mail_post_autofollow=0)).create(vals)
        # self.context.update({
        #     'mail_post_autofollow': False,
        #     'mail_create_nosubscribe': True,
        # })

    @api.model
    def write(self, vals):
        return super(MailThread, self.with_context(mail_create_nosubscribe=1,mail_post_autofollow=0)).write(vals)