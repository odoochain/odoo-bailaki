# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from datetime import timedelta


class ResPartnerRelation(models.Model):

    _inherit = 'res.partner.relation'

    @api.model
    def _cron_unmatch_relation_clean(self):
        """
            Verify and remove unmatches
        """
        unmatch_id = self.env.ref("bailaki.relation_type_unmatch")

        for relation in self.search([('type_id', '=', unmatch_id.id)]):
            if (relation.create_date):
                if (relation.create_date + timedelta(days=30) < fields.datetime.now()):
                    relation.unlink()

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def bailaki_SendLike(self, values):
        res = super(ResPartnerRelation, self).create(values)
        res_partner = self.sudo().env['res.partner'].search(
            [['id', '=', values[0]['left_partner_id']]]);
        if res_partner:
            res_partner._compute_match_relation();
            print(res_partner.name)
        return res
