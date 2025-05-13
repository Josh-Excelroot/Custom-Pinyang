#coding: utf-8

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class sticky_note(models.Model):
    """
    The model to keep sticky note info
    """
    _name = "sticky.note"
    _description = "Sticky Note"

    name = fields.Html(
        "Description",
        required=True,
    )
    res_model = fields.Char(string="Source Model")
    res_id = fields.Char(string="Source ID")
    color = fields.Selection(
        [
            ("#007bff", "blue"),
            ("#6610f2", "indigo"),
            ("#6f42c1", "purple"),
            ("#e83e8c", "pink"),
            ("#dc3545", "red"),
            ("#fd7e14", "orange"),
            ("#ffc107", "yellow"),
            ("#28a745", "green"),
            ("#20c997", "teal"),
            ("#17a2b8", "gray"),
            ("#6c757d", "gray"),
            ("#343a40", "gray-dark"),
        ],
        string="Color",
        default="#ffc107",
    )
    share = fields.Boolean(
        string="Share Note",
        help="""
            If checked a note would be visible for any user
            Otherwise for the author only
        """,
    )

    @api.multi
    def return_js_values(self):
        """
        The method to return js dict related to this note

        Returns:
         * js_dict: name, description, color

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
        }

    @api.model
    def return_notes(self, res_model, res_id):
        """
        The method to find all sticky notes related to this record and prepare them in js formats

        Args:
         * res_model - char - model name
         * res_id - int - id of a document

        Methods:
         * return_js_values

        Returns:
         * list of warning dicts:
          ** id
          ** name
          ** color
        """
        self = self.with_context(lang=self.env.user.lang)
        notes = self.search([
            ("res_model", "=", res_model),
            ("res_id", "=", res_id),
        ])
        res = []
        if notes:
            res = notes.mapped(lambda note: note.return_js_values())
        return res

    @api.multi
    def return_form_view(self, res_model=None, res_id=None):
        """
        The method to return new sticky note form view

        Args:
         * res_model - model name
         * res_id - id of document

        Returns:
         * dict for form view of sticky note
        """
        view_id = self.env.ref('sticky_notes.sticky_note_view_form').id
        context = self.env.context.copy()
        if res_model:
            context.update({
                "default_res_model": res_model,
                "default_res_id": res_id,
            })
        res = {
            "view_id": view_id,
            "context": context,
        }
        return res
