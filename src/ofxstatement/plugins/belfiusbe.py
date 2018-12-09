from ofxstatement.plugin import Plugin
from ofxstatement.parser import CsvStatementParser
from ofxstatement.statement import StatementLine, BankAccount
from ofxstatement.exceptions import ParseError
import csv
import re


LINELENGTH = 15
HEADER_START = "Rekening"

class BelfiusBePlugin(Plugin):
    """Belgian Belfius Bank plugin for ofxstatement
    """

    def get_parser(self, filename):
        f = open(filename, 'r')
        parser = BelfiusBeParser(f)
        return parser


class BelfiusBeParser(CsvStatementParser):

    date_format = "%d/%m/%Y"

    mappings = {
        'date': 9,
        'amount': 10,
        'memo': 14,
        'payee': 5,
    }

    # types = {
    #     'STORTING': 'DEP',
    #     'OVERSCHRIJVING': 'XFER',
    # }

    line_nr = 0

    def parse_float(self, value):
        """Return a float from a string with ',' as decimal mark.
        """
        return float(value.replace(',','.'))

    def split_records(self):
        """Return iterable object consisting of a line per transaction
        """
        return csv.reader(self.fin, delimiter=';')

    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object
        """
        self.line_nr += 1
        if line[0] == HEADER_START or len(line) != LINELENGTH:
            return None

        # Check the account id. Each line should be for the same account!
        if self.statement.account_id:
            if line[0] != self.statement.account_id:
                raise ParseError(self.line_nr,
                                 'AccountID does not match on all lines! ' +
                                 'Line has ' + line[0] + ' but file ' +
                                 'started with ' + self.statement.account_id)
        else:
            self.statement.account_id = line[0]

        # Check the currency. Each line should be for the same currency!
        if self.statement.currency:
            if line[11] != self.statement.currency:
                raise ParseError(self.line_nr,
                                 'Currency does not match on all lines! ' +
                                 'Line has ' + line[3] + ' but file ' +
                                 'started with ' + self.statement.currency)
        else:
            self.statement.currency = line[11]

        stmt_ln = super(BelfiusBeParser, self).parse_record(line)

        if line[4] != None and line[4] != '':
            stmt_ln.bank_account_to = BankAccount('', line[4])

        if stmt_ln.payee == None or stmt_ln.payee == '' and line[8].startswith('MAESTRO-BETALING'):
            payee_match = re.match('MAESTRO-BETALING\s+(?:.+?\s+)?\d\d/\d\d-[a-zA-Z0-9_-]*\s+(.+)\s+\w\w\s+\d+,', line[8])
            if payee_match != None:
                stmt_ln.payee = payee_match.group(1)

        refnum_match = re.search('REF. :\s*(\w+)', line[8])
        if refnum_match != None:
            stmt_ln.refnum = refnum_match.group(1)

        return stmt_ln
