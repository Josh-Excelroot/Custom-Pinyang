from bdb import effective
import email
import werkzeug
import json
import base64

from odoo import _, fields
from datetime import date
from odoo.exceptions import AccessError, MissingError
import odoo.http as http
from odoo.http import request
from odoo import SUPERUSER_ID
from datetime import datetime, timedelta, time
from odoo.addons.sale.controllers.portal import CustomerPortal as MainCustomerPortal
from odoo.addons.portal.controllers.portal import (
    CustomerPortal,
    pager as portal_pager,
    get_records_pager,
)
from odoo.addons.portal.controllers.mail import _message_post_helper

from odoo.osv import expression
from odoo.tools import consteq, plaintext2html


class Quotation(http.Controller):
    @http.route("/rfq_webform", type="http", auth="public", website=True)
    def rfq_webform(self, **kw):
        partner_id = http.request.env.user.partner_id.parent_id
        return http.request.render(
            "sci_goexcel_sq.create_rfq", {"partner_id": partner_id}
        )

    @http.route("/sales_quotation/create", type="http", auth="public", website=True)
    def rfq_create(self, **post):
        if post.get("debug"):
            return request.render("sci_goexcel_sq.rfq_thank_you")

        if post:
            state = "rfq"
            partner_id = int(post["partner_id"]) if "partner_id" in post else False
            effective_date = (
                post["effective_date"] if "effective_date" in post else False
            )
            expiry_date = post["expiry_date"] if "expiry_date" in post else False
            shipment_mode = post["shipment_mode"] if "shipment_mode" in post else False
            mode = post["mode"] if "mode" in post else False
            commodity1 = int(post["commodity1"]) if post["commodity1"] else False
            commodity_type = (
                int(post["commodity_type"]) if post["commodity_type"] else False
            )
            pol = int(post["pol"]) if post["pol"] else False
            pod = int(post["pod"]) if post["pod"] else False
            cargo_type = ''
            lcl_width = 0.00
            lcl_length = 0.00
            lcl_height = 0.00
            lcl_Weight = 0.00
            lcl_quantity = 0.00
            if post["cargo_type"]:

                cargo_type = post["cargo_type"]

            effective_date = (
                post["effective_date"] if "effective_date" in post else False
            )
            expiry_date = post["expiry_date"] if "expiry_date" in post else False
            hidden = int(post["hidden"]) if "hidden" in post else False

            container_type = 0
            container_quantity = 0
            weight = 0.00
            container_lines = 0

            if cargo_type == 'fcl':

                container_type = (
                    int(post["container_type"])
                )
                container_quantity = (
                    int(post["container_quantity"])
                    if "container_quantity" in post
                    else False
                )
                weight = float(post["weight"]) if "weight" in post else False

                container_lines = [
                    (
                        0,
                        0,
                        {
                            "container_type": container_type,
                            "container_quantity": container_quantity,
                            "weight": weight,
                            # "lcl_length": lcl_length,
                            # "lcl_width": lcl_width,
                            # "lcl_height": lcl_height,
                            # "lcl_Weight": lcl_Weight,
                            # "lcl_quantity": lcl_quantity,
                            # "volumetric_weight": volumetric_weight,
                            # "chargeable_weight": chargeable_weight,

                        },
                    )
                ]
                for i in range(2, hidden + 1):
                    container_type = (
                        int(post["container_type_" + str(i)])
                        if "container_type_" + str(i) in post
                        else False
                    )
                    container_quantity = (
                        int(post["container_quantity_" + str(i)])
                        if "container_quantity_" + str(i) in post
                        else False
                    )
                    weight = (
                        float(post["weight_" + str(i)])
                        if "weight_" + str(i) in post
                        else False
                    )
                    # lcl_length = (
                    #     float(post["lcl_length_" + str(i)])
                    #     if "lcl_length_" + str(i) in post
                    #     else False
                    # )
                    # lcl_width = (
                    #     float(post["lcl_width_" + str(i)])
                    #     if "lcl_width_" + str(i) in post
                    #     else False
                    # )
                    # lcl_height = (
                    #     float(post["lcl_height_" + str(i)])
                    #     if "lcl_height_" + str(i) in post
                    #     else False
                    # )
                    # lcl_weight = (
                    #     float(post["lcl_weight_" + str(i)])
                    #     if "lcl_weight_" + str(i) in post
                    #     else False
                    # )
                    # lcl_quantity = (
                    #     float(post["lcl_quantity_" + str(i)])
                    #     if "lcl_quantity_" + str(i) in post
                    #     else False
                    # )
                    # volumetric_weight = (
                    #     float(post["volumetric_weight_" + str(i)])
                    #     if "volumetric_weight_" + str(i) in post
                    #     else False
                    # )
                    # chargeable_weight = (
                    #     float(post["chargeable_weight_" + str(i)])
                    #     if "chargeable_weight_" + str(i) in post
                    #     else False
                    # )

                    container_lines.append(
                        (
                            0,
                            0,
                            {
                                "container_type": container_type,
                                "container_quantity": container_quantity,
                                "weight": weight,
                                # "lcl_length": lcl_length,
                                # "lcl_width": lcl_width,
                                # "lcl_height": lcl_height,
                                # "lcl_weight": lcl_weight,
                                # "lcl_quantity": lcl_quantity,
                                # "volumetric_weight": volumetric_weight,
                                # "chargeable_weight": chargeable_weight,
                            },
                        )
                    )
            elif cargo_type == 'lcl':
                lcl_length = (
                    int(post["lcl_length"])
                    if "lcl_length" in post
                    else False
                )
                lcl_width = (
                    int(post["lcl_width"])
                    if "lcl_width" in post
                    else False
                )

                lcl_height = (
                    int(post["lcl_height"])
                    if "lcl_height" in post
                    else False
                )

                lcl_Weight = (
                    int(post["lcl_Weight"])
                    if "lcl_Weight" in post
                    else False
                )

                lcl_quantity = (
                    int(post["lcl_quantity"])
                    if "lcl_quantity" in post
                    else False
                )

                # volumetric_weight = (
                #     int(post["volumetric_weight"])
                #     if "volumetric_weight" in post
                #     else False
                # )
                # chargeable_weight = (
                #     int(post["chargeable_weight"])
                #     if "chargeable_weight" in post
                #     else False
                # )

            vals = {
                "partner_id": partner_id,
                "state": state,
                "service_type": shipment_mode,
                "mode": mode,
                "commodity1": commodity1,
                "POL": pol,
                "POD": pod,
                "type": cargo_type,
                "container_lines": container_lines,
                "effect_date": effective_date,
                "expiry_date": expiry_date,
                "type_name": "Quotation",
                "channel": "portal",
                "lcl_length": lcl_length,
                "lcl_width": lcl_width,
                "lcl_height": lcl_height,
                "lcl_Weight": lcl_Weight,
                "lcl_quantity": lcl_quantity,
                # "volumetric_weight": volumetric_weight,
                # "chargeable_weight": chargeable_weight,
            }

            sales_quotation_obj = request.env["sale.order"].sudo().create(vals)

            return request.render("sci_goexcel_sq.rfq_thank_you")


# class PortalInherit(MainCustomerPortal):
#     @http.route(
#         ["/my/quotes", "/my/quotes/page/<int:page>"],
#         type="http",
#         auth="user",
#         website=True,
#     )
#     def portal_my_quotes(
#         self, page=1, date_begin=None, date_end=None, sortby=None, **kw
#     ):
#         values = self._prepare_portal_layout_values()
#         partner = request.env.user.partner_id
#         SaleOrder = request.env["sale.order"]

#         domain = [
#             ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
#             ("state", "in", ["sent", "cancel", "rfq", "done"]),
#         ]

#         searchbar_sortings = {
#             "date": {"label": _("Order Date"), "order": "date_order desc"},
#             "name": {"label": _("Reference"), "order": "name"},
#             "stage": {"label": _("Stage"), "order": "state"},
#         }

#         # default sortby order
#         if not sortby:
#             sortby = "date"
#         sort_order = searchbar_sortings[sortby]["order"]

#         archive_groups = self._get_archive_groups("sale.order", domain)
#         if date_begin and date_end:
#             domain += [
#                 ("create_date", ">", date_begin),
#                 ("create_date", "<=", date_end),
#             ]

#         # count for pager
#         quotation_count = SaleOrder.search_count(domain)
#         # make pager
#         pager = portal_pager(
#             url="/my/quotes",
#             url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
#             total=quotation_count,
#             page=page,
#             step=self._items_per_page,
#         )
#         # search the count to display, according to the pager data
#         quotations = SaleOrder.search(
#             domain, order=sort_order, limit=self._items_per_page, offset=pager["offset"]
#         )
#         request.session["my_quotations_history"] = quotations.ids[:100]

#         values.update(
#             {
#                 "date": date_begin,
#                 "quotations": quotations.sudo(),
#                 "page_name": "quote",
#                 "pager": pager,
#                 "archive_groups": archive_groups,
#                 "default_url": "/my/quotes",
#                 "searchbar_sortings": searchbar_sortings,
#                 "sortby": sortby,
#             }
#         )
#         res = super(PortalInherit, self).portal_my_quotes(
#             self, page=1, date_begin=None, date_end=None, sortby=None, **kw
#         )
#         return res


class CustomerPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        SaleOrder = request.env["sale.order"]

        quotation_count = SaleOrder.search_count(
            [
                # (
                #     "message_partner_ids",
                #     "child_of",
                #     [partner.commercial_partner_id.id],
                # ),
                ("state", "in", ["sent", "cancel", "done", "rfq", "confirm"]),
            ]
        )


        order_count = (
            SaleOrder.search_count(
                [
                    (
                        "message_partner_ids",
                        "child_of",
                        [partner.commercial_partner_id.id],
                    ),
                    ("state", "in", ["sale", "done", "rfq", "cancel", ]),
                ]
            )
            if SaleOrder.check_access_rights("read", raise_exception=False)
            else 0
        )

        values.update(
            {"quotation_count": quotation_count, "order_count": order_count, }
        )
        return values

    @http.route(
        ["/my/quotes", "/my/quotes/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_quotes(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env["sale.order"]

        domain = [
            # ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ("state", "in", ["sent", "cancel", "rfq", "done", "confirm"]),
        ]

        searchbar_sortings = {
            "date": {"label": _("Order Date"), "order": "date_order desc"},
            "name": {"label": _("Reference"), "order": "name"},
            "stage": {"label": _("Stage"), "order": "state"},
        }

        # default sortby order
        if not sortby:
            sortby = "date"
        sort_order = searchbar_sortings[sortby]["order"]

        archive_groups = self._get_archive_groups("sale.order", domain)
        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        # count for pager
        quotation_count = SaleOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/quotes",
            url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page,
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.search(
            domain, order=sort_order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_quotations_history"] = quotations.ids[:100]

        values.update(
            {
                "date": date_begin,
                "quotations": quotations.sudo(),
                "page_name": "quote",
                "pager": pager,
                "archive_groups": archive_groups,
                "default_url": "/my/quotes",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("sale.portal_my_quotations", values)

    @http.route(["/my/orders/<int:order_id>"], type="http", auth="public", website=True)
    def portal_order_page(
            self,
            order_id,
            report_type=None,
            access_token=None,
            message=False,
            download=False,
            **kw
    ):
        try:
            order_sudo = self._document_check_access(
                "sale.order", order_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        if report_type in ("html", "pdf", "text"):
            return self._show_report(
                model=order_sudo,
                report_type=report_type,
                report_ref="sale.action_report_saleorder",
                download=download,
            )

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        # Log only once a day
        if order_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get("view_quote_%s" % order_sudo.id)
            if isinstance(session_obj_date, date):
                session_obj_date = session_obj_date.isoformat()
            if session_obj_date != now and request.env.user.share and access_token:
                request.session["view_quote_%s" % order_sudo.id] = now
                body = _("Quotation viewed by customer")
                _message_post_helper(
                    res_model="sale.order",
                    res_id=order_sudo.id,
                    message=body,
                    token=order_sudo.access_token,
                    message_type="notification",
                    subtype="mail.mt_note",
                    partner_ids=order_sudo.user_id.sudo().partner_id.ids,
                )

        values = {
            "sale_order": order_sudo,
            "message": message,
            "token": access_token,
            "return_url": "/shop/payment/validate",
            "bootstrap_formatting": True,
            "partner_id": order_sudo.partner_id.id,
            "report_type": "html",
        }
        if order_sudo.company_id:
            values["res_company"] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND(
                [
                    [
                        "&",
                        ("website_published", "=", True),
                        ("company_id", "=", order_sudo.company_id.id),
                    ],
                    [
                        "|",
                        ("specific_countries", "=", False),
                        ("country_ids", "in", [order_sudo.partner_id.country_id.id]),
                    ],
                ]
            )
            acquirers = request.env["payment.acquirer"].sudo().search(domain)

            values["acquirers"] = acquirers.filtered(
                lambda acq: (acq.payment_flow == "form" and acq.view_template_id)
                            or (acq.payment_flow == "s2s" and acq.registration_view_template_id)
            )
            values["pms"] = request.env["payment.token"].search(
                [("partner_id", "=", order_sudo.partner_id.id)]
            )

        if order_sudo.state in ("draft", "sent", "cancel", "rfq"):
            history = request.session.get("my_quotations_history", [])
        else:
            history = request.session.get("my_orders_history", [])
        values.update(get_records_pager(history, order_sudo))

        return request.render("sale.sale_order_portal_template", values)
