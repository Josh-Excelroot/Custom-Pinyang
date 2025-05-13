from odoo import api, fields, models, exceptions
import logging
import ast
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    branch_ids = fields.Many2many("account.analytic.tag", string="Branch")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for field in doc.xpath("//field[@name='child_ids']"):
                context_str = field.get('context') \
                    .replace("'default_customer': customer", "'default_customer': False") \
                    .replace("'default_supplier': supplier", "'default_supplier': False")
                field.set('context', context_str)
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def create(self, vals):
        print('>>>>>>>>>>>>> sci_goexcel_branch create 1')
        # if not vals["branch_ids"]:
        #     print("test")
        #     vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
        #     # vals['branch'] = self.env.user.default_branch.id
        #     branch_list = []
        #     branchs = vals.get("branch_ids")[0]
        #     branchs = branchs[2]
        #     # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
        #     for branch in branchs:
        #         category_id = self.env["account.analytic.tag"].browse(branch)
        #     category = self.env["res.partner.category"].search(
        #         [("name", "=", category_id.name)]
        #     )
        #     branch_list.append(category.id)
        #     vals["category_id"] = [(6, 0, branch_list)]
        #     # vals['category_id'] = [(6, 0, [category.id])]
        # res = super(ResPartner, self).create(vals)

        # if vals.get("branch_ids") and vals.get("category_id"):
        #     vals["category_id"] = vals["category_id"]
        #     vals["branch_ids"] = vals["branch_ids"]
            #res = super(ResPartner, self).create(vals)
        if vals.get("branch_ids") and not vals.get("category_id"):
            # vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
            # vals['branch'] = self.env.user.default_branch.id
            print('>>>>>>>>>>>>> sci_goexcel_branch create 2')
            branch_list = []
            branchs = vals.get("branch_ids")[0]
            branchs = branchs[2]
            # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
            for branch in branchs:
                category_id = self.env["account.analytic.tag"].browse(branch)
            category = self.env["res.partner.category"].search(
                [("name", "=", category_id.name)]
            )
            branch_list.append(category.id)
            vals["category_id"] = [(6, 0, branch_list)]
            # vals['category_id'] = [(6, 0, [category.id])]
            #res = super(ResPartner, self).create(vals)
        elif vals.get("category_id") and not vals.get("branch_ids"):
            print('>>>>>>>>>>>>> sci_goexcel_branch create 3')
            vals["category_id"] = vals["category_id"]
            # vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
            # vals['branch'] = self.env.user.default_branch.id
            catogory_list = []
            category = vals.get("category_id")[0]
            category = category[2]
            # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
            for categories in category:
                branch_id = self.env["res.partner.category"].browse(categories)

            branch = self.env["account.analytic.tag"].search(
                [("name", "=", branch_id.name)]
            )
            catogory_list.append(branch.id)
            vals["branch_ids"] = [(6, 0, catogory_list)]
        print('>>>>>>>>>>>>> sci_goexcel_branch create 4')
        res = super(ResPartner, self).create(vals)
        #
        return res

    @api.multi
    def write(self, vals):
        print('>>>>>>>>>>>>> sci_goexcel_branch write 1')
        # if vals.get("branch_ids") and vals.get("category_id"):
        #     vals["category_id"] = vals["category_id"]
        #     vals["branch_ids"] = vals["branch_ids"]
            #res = super(ResPartner, self).write(vals)
        # if not vals.get("branch_ids") and not vals.get("category_id"):
        #     vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
        #     # vals['branch'] = self.env.user.default_branch.id
        #     branch_list = []
        #     branchs = vals.get("branch_ids")[0]
        #     branchs = branchs[2]
        #     # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
        #     for branch in branchs:
        #         category_id = self.env["account.analytic.tag"].browse(branch)
        #     category = self.env["res.partner.category"].search(
        #         [("name", "=", category_id.name)]
        #     )
        #     branch_list.append(category.id)
        #     vals["category_id"] = [(6, 0, branch_list)]
        #     # vals['category_id'] = [(6, 0, [category.id])]
        #     #res = super(ResPartner, self).create(vals)
        # elif vals.get("category_id") and not vals.get("branch_ids"):
        #     vals["category_id"] = vals["category_id"]
        #     # vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
        #     # vals['branch'] = self.env.user.default_branch.id
        #     catogory_list = []
        #     category = vals.get("category_id")[0]
        #     category = category[2]
        #     # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
        #     for categories in category:
        #         branch_id = self.env["res.partner.category"].browse(categories)
        #
        #     branch = self.env["account.analytic.tag"].search(
        #         [("name", "=", branch_id.name)]
        #     )
        #     catogory_list.append(branch.id)
        #     vals["branch_ids"] = [(6, 0, catogory_list)]
        res = super(ResPartner, self).write(vals)
        return res
        # if vals.get("branch_ids") and vals.get("category_id"):
        #     vals["category_id"] = vals["category_id"]
        #     vals["branch_ids"] = vals["branch_ids"]
        #     res = super(ResPartner, self).create(vals)
        # elif not vals.get("branch_ids") and not vals.get("category_id"):
        #     vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
        #     # vals['branch'] = self.env.user.default_branch.id
        #     branch_list = []
        #     branchs = vals.get("branch_ids")[0]
        #     branchs = branchs[2]
        #     # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
        #     for branch in branchs:
        #         category_id = self.env["account.analytic.tag"].browse(branch)
        #     category = self.env["res.partner.category"].search(
        #         [("name", "=", category_id.name)]
        #     )
        #     branch_list.append(category.id)
        #     vals["category_id"] = [(6, 0, branch_list)]
        #     # vals['category_id'] = [(6, 0, [category.id])]
        #     res = super(ResPartner, self).create(vals)
        # elif vals.get("category_id") and not vals.get("branch_ids"):
        #     vals["category_id"] = vals["category_id"]
        #     # vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
        #     # vals['branch'] = self.env.user.default_branch.id
        #     catogory_list = []
        #     category = vals.get("category_id")[0]
        #     category = category[2]
        #     # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
        #     for categories in category:
        #         branch_id = self.env["res.partner.category"].browse(categories)
        #
        #     branch = self.env["account.analytic.tag"].search(
        #         [("name", "=", branch_id.name)]
        #     )
        #     catogory_list.append(branch.id)
        #     vals["branch_ids"] = [(6, 0, catogory_list)]
        # if vals.get("branch_ids"):
        #     branch_list = []
        #     brands = vals.get("branch_ids")[0]
        #     brands = brands[2]
        #     print(brands)
        #     for brand in brands:
        #         branch_name = self.env["account.analytic.tag"].browse(brand)
        #         category = self.env["res.partner.category"].search(
        #             [("name", "=", branch_name.name)]
        #         )
        #         branch_list.append(category.id)
        #     vals["category_id"] = [(6, 0, branch_list)]
        # res = super(ResPartner, self).create(vals)
        #     #
        # return res
    #     if vals.get("branch_ids"):
    #         branch_list = []
    #         brands = vals.get("branch_ids")[0]
    #         brands = brands[2]
    #         print(brands)
    #         for brand in brands:
    #             branch_name = self.env["account.analytic.tag"].browse(brand)
    #             category = self.env["res.partner.category"].search(
    #                 [("name", "=", branch_name.name)]
    #             )
    #             branch_list.append(category.id)
    #         vals["category_id"] = [(6, 0, branch_list)]
    #     print(vals)

        # if vals["branch_ids"] and vals["category_id"]:
        #     vals["category_id"] = vals["category_id"]
        #     vals["branch_ids"] = vals["branch_ids"]
        #     res = super(ResPartner, self).create(vals)
        # elif not vals["branch_ids"] and not vals["category_id"]:
        #     vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
        #     # vals['branch'] = self.env.user.default_branch.id
        #     branch_list = []
        #     branchs = vals.get("branch_ids")[0]
        #     branchs = branchs[2]
        #     # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
        #     for branch in branchs:
        #         category_id = self.env["account.analytic.tag"].browse(branch)
        #     category = self.env["res.partner.category"].search(
        #         [("name", "=", category_id.name)]
        #     )
        #     branch_list.append(category.id)
        #     vals["category_id"] = [(6, 0, branch_list)]
        #     # vals['category_id'] = [(6, 0, [category.id])]
        #     res = super(ResPartner, self).create(vals)
        # elif vals["category_id"] and not vals["branch_ids"]:
        #     vals["category_id"] = vals["category_id"]
        #     # vals["branch_ids"] = [(6, 0, [self.env.user.default_branch.id])]
        #     # vals['branch'] = self.env.user.default_branch.id
        #     catogory_list = []
        #     category = vals.get("category_id")[0]
        #     category = category[2]
        #     # branch_name = self.env['account.analytic.tag'].browse(vals['branch_ids'])
        #     for categories in category:
        #         branch_id = self.env["res.partner.category"].browse(categories)
        #
        #     branch = self.env["account.analytic.tag"].search(
        #         [("name", "=", branch_id.name)]
        #     )
        #     catogory_list.append(branch.id)
        #     vals["branch_ids"] = [(6, 0, catogory_list)]
        #
        # res = super(ResPartner, self).write(vals)
        # return res

        # if not vals.get("branch_ids") and vals.get("category_id"):
        #     # Set branch_ids based on category_id
        #     category = self.env["res.partner.category"].browse(vals["category_id"])
        #     branches = self.env["account.analytic.tag"].search(
        #         [("name", "=", category.name)]
        #     )
        #     vals["branch_ids"] = [(6, 0, [branch.id for branch in branches])]
        # res = super(ResPartner, self).create(vals)
        # return res

        # if vals.get("branch_ids"):
        #     branch_list = []
        #     brands = vals.get("branch_ids")[0]
        #     brands = brands[2]
        #     print(brands)
        #     for brand in brands:
        #         branch_name = self.env["account.analytic.tag"].browse(brand)
        #         category = self.env["res.partner.category"].search(
        #             [("name", "=", branch_name.name)]
        #         )
        #         branch_list.append(category.id)
        #     vals["category_id"] = [(6, 0, branch_list)]
        # print(vals)
