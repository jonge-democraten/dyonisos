#!/usr/bin/env python

# payDEAL - the iDEAL module for Python
# file:		IssuerEntry.py
# author:	Wai Yi Leung <w.y.leung@e-sensei.nl>
# website:	http://paydeal.e-sensei.nl/
# desc:		IssuerEntry handling

class IssuerEntry(object):
	"""
		Issuer 'Bean' object
	"""
	def __init__( self ):
		self.issuerID	= ''
		self.issuerListType	= ''
		self.issuerName	= ''

	def toString( self ):
		""" toString
			@return Returns a readable representation of the IssuerEntry
		"""
		return u'IssuerBean: issuerID=%s issuerName=%s issuerList=%s' % ( self.getIssuerID(), self.getIssuerName(), self.getIssuerListType() )

	def setIssuerID( self, issuerID ):
		""" setIssuerID
			@param issuerID The issuerID to set.
		"""
		self.issuerID = issuerID

	def getIssuerID( self ):
		""" getIssuerID
			@return Returns the issuerID.
		"""
		return self.issuerID

	def setIssuerListType( self, issuerListType ):
		""" setIssuerList
			@param issuerList The issuerList to set.
		"""
		self.issuerListType = issuerListType

	def getIssuerListType( self ):
		""" getIssuerListType
			@return Returns the IssuerListType. ("Short", "Long")
		"""
		return self.issuerListType

	def setIssuerName( self, issuerName ):
		""" setIssuerName
			@param issuerName The issuerName to set.
		"""
		self.issuerName = issuerName

	def getIssuerName( self ):
		""" getIssuerName
			@return Returns the issuerName.
		"""
		return self.issuerName

