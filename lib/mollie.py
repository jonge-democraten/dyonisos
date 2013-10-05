import pycurl
import cStringIO
from lxml import objectify
import logging
import urllib

# Based on https://www.mollie.nl/support/documentatie/betaaldiensten/ideal

ERR_IMPROPER_INPUT_VALUE =  -1
ERR_NO_PARTNERID =          -2
ERR_IMPROPER_REPORTURL =    -3
ERR_NO_AMOUNT =             -4
ERR_NO_BANK_ID =            -5
ERR_UNKNOWN_BANK_ID =       -6
ERR_NO_DESCRIPTION =        -7
ERR_NO_TRANSACTION_ID =     -8
ERR_ILLIGAL_CHARACTERS =    -9
ERR_UNKNOWN_ORDER =         -10
ERR_NO_PARTERID =           -11
ERR_IMPROPER_RETURNURL =    -12
ERR_LOGIN_REQUIRED =        -13
ERR_AMOUNT_TOO_LOW =        -14
ERR_ACCOUNT_NOT_ALLOWED =   -15
ERR_UNKNOWN_PROFILE =       -16
ERR_RETURNURL_INVALID =     -17


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
        yield bank
        
def fetch(partnerid, amount, bank_id, description, reporturl, returnurl, profile_key=None):
    params = urllib.urlencode({
        "a": "fetch",
        "partnerid": partnerid,
        "amount": amount,
        "bank_id": "%04d" % (bank_id),
        "description": description,
        "reporturl": reporturl,
        "returnurl": returnurl,
        "profile_key": profile_key
    })
    response = httpsrequest("https://www.mollie.nl/xml/ideal?%s" % params)
    obj = objectify.fromstring(response)
    order = obj.order
    return order
            
def check():
    params = urllib.urlencode({
        "a": "check",
        "partnerid": partnerid,
        "transaction_id": transaction_id
    })
    response = httpsrequest("https://secure.mollie.nl/xml/ideal?%s" % params)
    obj = objectify.fromstring(response)
    return obj.order
    
    

    
    
    
