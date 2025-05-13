# Copyright 2009 Camptocamp
# Copyright 2009 Grzegorz Grzelak
# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
from datetime import date, timedelta
from urllib.request import urlopen
import xml.sax
from xml.sax import make_parser

import requests #pip install requests
from odoo import models, fields, api


class ResCurrencyRateProviderECB(models.Model):
    _inherit = 'res.currency.rate.provider'

    service = fields.Selection(
        selection_add=[('ECB', 'European Central Bank'),
                       ("BNM", "Bank Negara Malaysia")],
    )

    #Modified_Lo
    @api.multi
    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service == 'ECB':
            # List of currencies obtained from:
            # https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip
            return \
                [
                    'USD', 'JPY', 'BGN', 'CYP', 'CZK', 'DKK', 'EEK', 'GBP',
                    'HUF', 'LTL', 'LVL', 'MTL', 'PLN', 'ROL', 'RON', 'SEK',
                    'SIT', 'SKK', 'CHF', 'ISK', 'NOK', 'HRK', 'RUB', 'TRL',
                    'TRY', 'AUD', 'BRL', 'CAD', 'CNY', 'HKD', 'IDR', 'ILS',
                    'INR', 'KRW', 'MXN', 'MYR', 'NZD', 'PHP', 'SGD', 'THB',
                    'ZAR', 'EUR'
                ]
        elif self.service == 'BNM':
            # List of currencies obtained from:
            # https://www.bnm.gov.my/exchange-rates
            return [
                "USD", "GBP", "EUR", "JPY100", "CHF", "AUD", "CAD", "SGD",
                "HKD100", "THB100", "PHP100", "TWD100", "KRW100", "IDR100", "SAR100", "SDR",
                "CNY", "BND", "VND100", "KHR100", "NZD", "MMK100", "INR100", "AED100",
                "PKR100", "NPR100", "EGP", 'MYR'
            ]
        else:
            return super()._get_supported_currencies()  # pragma: no cover


    def convert_json_to_dictionary(self, base_currency, currencies, date_from, date_to, data):
        def default_value():
            return {}

        rate_dict = defaultdict(default_value)
        for each in data:
            if each['currency_code'] in currencies:
                each_rate = each['rate']
                rate_dict[each_rate['date']][each['currency_code']] = each_rate['middle_rate']
        return rate_dict

    @api.multi
    def _obtain_rates(self, base_currency, currencies, date_from, date_to, api_url):
        self.ensure_one()
        if self.service == 'ECB':
            invert_calculation = False
            if base_currency != 'EUR':
                invert_calculation = True
                if base_currency not in currencies:
                    currencies.append(base_currency)

            # Depending on the date range, different URLs are used
            url = 'https://www.ecb.europa.eu/stats/eurofxref'
            if date_from == date_to and date_from == date.today():
                url = url + '/eurofxref-daily.xml'
            elif (date.today() - date_from) / timedelta(days=90) < 1.0:
                url = url + '/eurofxref-hist-90d.xml'
            else:
                url = url + '/eurofxref-hist.xml'

            handler = EcbRatesHandler(currencies, date_from, date_to)
            with urlopen(url) as response:
                parser = make_parser()
                parser.setContentHandler(handler)
                parser.parse(response)
            content = handler.content
            if invert_calculation:
                for k in content.keys():
                    base_rate = float(content[k][base_currency])
                    for rate in content[k].keys():
                        content[k][rate] = str(float(content[k][rate])/base_rate)
                    content[k]['EUR'] = str(1.0/base_rate)
            return content
        elif self.service == 'BNM':
            invert_calculation = False
            if base_currency != 'MYR':
                invert_calculation = True
                if base_currency not in currencies:
                    currencies.append(base_currency)

            request = _send_get_request(api_url)# returns JSON
            data = request.json()['data']
            rate_dict = self.convert_json_to_dictionary(base_currency, currencies, 1, 2, data)
            if invert_calculation:
                for k in rate_dict.keys():
                    base_rate = float(rate_dict[k][base_currency])
                    for rate in rate_dict[k].keys():
                        rate_dict[k][rate] = str(float(rate_dict[k][rate])/base_rate)
                    rate_dict[k]['MYR'] = str(1.0/base_rate)
            elif invert_calculation == False:
                for k in rate_dict.keys():
                    rate_dict[k]['MYR'] = str(1.0)
            print(rate_dict)
            return rate_dict
        else:
            return super()._obtain_rates(base_currency, currencies, date_from,
                                         date_to)  # pragma: no cover

def _send_get_request(req_url):
    headers = {
        "Accept": "application/vnd.BNM.API.v1+json"
    }
    # Send request
    r = requests.get(req_url, headers=headers)

    # Handle Response
    if r.status_code == 200 or r.status_code == 201:
        return r
    else:
        print("failed to get data from api call")
        raise ValueError("failed to get data from api call, please check if the provided api is valid")

# FOR XML
class EcbRatesHandler(xml.sax.ContentHandler):
    def __init__(self, currencies, date_from, date_to):
        self.currencies = currencies
        self.date_from = date_from
        self.date_to = date_to
        self.date = None
        self.content = defaultdict(dict)

    def startElement(self, name, attrs):
        if name == 'Cube' and 'time' in attrs:
            self.date = fields.Date.from_string(attrs['time'])
        elif name == 'Cube' and \
                all([x in attrs for x in ['currency', 'rate']]):
            currency = attrs['currency']
            rate = attrs['rate']
            if (self.date_from is None or self.date >= self.date_from) and \
                    (self.date_to is None or self.date <= self.date_to) and \
                    currency in self.currencies:
                self.content[self.date.isoformat()][currency] = rate
