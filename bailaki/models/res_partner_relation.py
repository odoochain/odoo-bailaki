# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from datetime import timedelta


class ResPartnerRelation(models.Model):

    _inherit = 'res.partner.relation'

    date_start = fields.Date(
        'Starting date',
        required=True,
        default=fields.Date.today
    )

    @api.model
    def _cron_unmatch_relation_clean(self):
        """
            Verify and remove unmatches
        """
        unmatch_id = self.env.ref("bailaki.relation_type_unmatch")

        for relation in self.search([('type_id', '=', unmatch_id.id)]):
            if (relation.date_start):
                if (relation.date_start + timedelta(days=30) < fields.date.today()):
                    relation.unlink()
