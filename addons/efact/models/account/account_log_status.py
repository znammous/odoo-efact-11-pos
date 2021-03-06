from odoo import api,models,fields
from ..auth import oauth
import requests
import json
from odoo.exceptions import UserError,ValidationError

class AccountLogStatus(models.Model):
    _name = "account.log.status"
    _order = "create_date desc"

    name = fields.Char("Nombre")
    api_user_id = fields.Char("API User id")
    content_xml = fields.Text("Respuesta de SUNAT base64 ZIP")
    description = fields.Char("Descripción")
    response_xml = fields.Text("Respuesta de SUNAT - Formateado")
    request_json = fields.Text("Contenido de Comprobante en JSON")
    signed_xml = fields.Text("Envío de comprobante ZIP en base64")
    response_json = fields.Text("Respuesta del API")
    unsigned_xml = fields.Text("Comprobante sin Firmar")
    signed_xml_data = fields.Text("Comprobante XML Firmado - Formateado")
    
    signed_xml_data_without_format = fields.Text("Comprobante XML Firmado")
    response_xml_without_format = fields.Text("Respuesta de Sunat - CDR")

    status = fields.Text("Estado de envío a SUNAT")
    date_request = fields.Date("Fecha de Envío al API")
    date_issue = fields.Date("Fecha de Emisión a SUNAT")
    api_request_id = fields.Char("Identificador de Envío")
    digest_value = fields.Char("Digest Value")

    account_invoice_id = fields.Many2one("account.invoice",string="Comprobante")
    account_summary_id = fields.Many2one("account.summary",string="Resumen Diario")
    guia_remision_id = fields.Many2one("efact.guia_remision",string="Guía de Remisión")
    company_id = fields.Many2one("res.company",
                                    string="Compañia",
                                    default=lambda self: self.env.user.company_id.id)

    def update_request_response_xml(self):
        for log in self:
            company = self.company_id or self.env.user.company_id
            token = oauth.generate_token_by_company(company)
            data = {
                "method": "Log.get_log",
                "kwargs":{
                    "id": log.api_request_id
                }
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": token
            }
            r = requests.post(company.endpoint, headers=headers,data=json.dumps(data))

            if r.status_code == 200:
                response = r.json()
                if "result" in response:
                    result = response.get("result")
                    log.signed_xml_data_without_format = result.get("signed_xml","")
                    log.response_xml_without_format = result.get("sunat_response_xml","")
            else:
                raise UserError(r.text)