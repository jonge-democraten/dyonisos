#!/usr/bin/env python

# payDEAL - the iDEAL module for Python
# file:		AcquirerStatusResponse.py
# author:	Wai Yi Leung <w.y.leung@e-sensei.nl>
# website:	http://paydeal.e-sensei.nl/
# desc:		Class for storing the AcquirerStatusResponse with customer information and transactionstatus

class AcquirerStatusResponse( object ):
	"""
		This class contains all necessary data that can be returned from a iDEAL AcquirerTrxRequest.
	"""
	def __init__( self ):
		self.acquirerID		= ''
		self.consumerName	= ''
		self.consumerAccountNumber = ''
		self.consumerCity	= ''
		self.transactionID	= ''
		self.status			= ''
		self.errorMessage	= False

	def getAcquirerID( self ):
		"""
			@return Returns the acquirerID.
		"""
		return self.acquirerID

	def setAcquirerID( self, acquirerID ):
		"""
			@param acquirerID The acquirerID to set. (mandatory)
		"""
		self.acquirerID = acquirerID

	def getConsumerAccountNumber( self ):
		"""
			@return Returns the consumerAccountNumber.
		"""
		return self.consumerAccountNumber

	def setConsumerAccountNumber( self, consumerAccountNumber ):
		"""
			@param consumerAccountNumber The consumerAccountNumber to set.
		"""
		self.consumerAccountNumber = consumerAccountNumber

	def getConsumerCity( self ):
		"""
			@return Returns the consumerCity.
		"""
		return self.consumerCity

	def setConsumerCity( self, consumerCity ):
		"""
			@param consumerCity The consumerCity to set.
		"""
		self.consumerCity = consumerCity

	def getConsumerName( self ):
		"""
			@return Returns the consumerName.
		"""
		return self.consumerName

	def setConsumerName( self, consumerName ):
		"""
			@param consumerName The consumerName to set.
		"""
		self.consumerName = consumerName

	def getTransactionID( self ):
		"""
			@return Returns the transactionID.
		"""
		return self.transactionID

	def setTransactionID( self, transactionID ):
		"""
			@param transactionID The transactionID to set.
		"""
		self.transactionID = transactionID

	def getStatus( self ):
		"""
			@return Returns the status. See the definitions
		"""
		return self.status

	def setStatus( self, status ):
		"""
			@param status The status to set. See the definitions
		"""
		self.status = status

	def IsResponseError( self ):
		return False
