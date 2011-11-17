#!/usr/bin/env python

# payDEAL - the iDEAL module for Python
# file:		fetchIssuers.py
# author:	Wai Yi Leung <w.y.leung@e-sensei.nl>
# website:	http://paydeal.e-sensei.nl/
# desc:		This script is for testing the directory response.

from ideal import *

oIDC = iDEALConnector()
issuers = oIDC.GetIssuerList()

# lijst van banken als het gelukt is, anders error
if issuers.IsResponseError():
	print issuers.getErrorCode()
	print issuers.getErrorMessage()
else:
	print issuers.getAcquirerID()
	print issuers.getDirectoryDateTimeStamp()
	dIssuers = issuers.getIssuerFullList()
	for sIS, oIS in dIssuers.items():
		print oIS.getIssuerID()
		print oIS.getIssuerListType()
		print oIS.getIssuerName()
#	print issuers.getIssuerShortList()
#	print issuers.getIssuerLongList()
