#!/usr/bin/env python

# payDEAL - the iDEAL module for Python
# file:		DirectoryResponse.py
# author:	Wai Yi Leung <w.y.leung@e-sensei.nl>
# website:	http://paydeal.e-sensei.nl/
# desc:		Class for storing the DirectoryResponse

from IssuerEntry import *

class DirectoryResponse( object ):
	"""
		DirectoryResponse holds the information received from the Acquirer about the available Issuers
	"""
	def __init__( self ):
		self.acquirerID			= ''
		self.directoryDateTime	= ''
		self.issuerShortList	= {}
		self.issuerLongList		= {}
		self.errorMessage		= False

	def getIssuerShortList( self ):
		"""
			@return Returns a list if IssuerEntry objects for the short listing only.
			The List contains all Issuers that were sent by the acquirer System during the Directory Request.
			The Issuers are stored as IssuerEntry objects.
		"""
		return self.issuerShortList

	def getIssuerLongList( self ):
		return self.issuerLongList

	def getIssuerFullList( self ):
		#self.issuerShortList.sort()
		#self.issuerLongList.sort()
		tmp = self.getIssuerShortList().copy()
		tmp.update( self.getIssuerLongList().copy() )
		return tmp

	def getAcquirerID( self ):
		"""
			@return Returns the acquirerID from the answer XML message.
		"""
		return self.acquirerID

	def setAcquirerID( self, acquirerID ):
		"""
			@param sets the acquirerID
		"""
		self.acquirerID = acquirerID

	def getDirectoryDateTimeStamp( self ):
		"""
			@return Returns the directory date/time stamp from the response XML message.
		"""
		return self.directoryDateTime

	def setDirectoryDateTimeStamp( self, directoryDateTime ):
		"""
			@param sets the directory date time stamp
		"""
		self.directoryDateTime = directoryDateTime

	def addIssuer( self, entry ):
		"""
			adds an Issuer to the IssuerList
		"""
		if isinstance( entry, IssuerEntry ):
			if entry.getIssuerListType() == 'short':
				self.issuerShortList[ entry.getIssuerName() ] = entry
				# python cannot sort on dicts
			else:
				self.issuerLongList[ entry.getIssuerName() ] = entry

	def IsResponseError( self ):
		return False
