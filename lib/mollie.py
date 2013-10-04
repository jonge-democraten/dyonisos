import pycurl
import cStringIO
from lxml import objectify
import logging


def httpsrequest(url):
    buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.setopt(c.SSL_VERIFYHOST, 2)
    c.perform()
    val = buf.getvalue()
    buf.close()
    return val
    

def banklist():
    response = httpsrequest('https://secure.mollie.nl/xml/ideal?a=banklist')
    obj = objectify.fromstring(response)
    logging.info(obj.message)
    for bank in obj.bank:
        yield (bank.bank_id, bank.bank_name)
