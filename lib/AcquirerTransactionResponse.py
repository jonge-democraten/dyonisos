#!/usr/bin/env python

# payDEAL - the iDEAL module for Python
# file:		AcquirerTransactionResponse.py
# author:	Wai Yi Leung <w.y.leung@e-sensei.nl>
# website:	http://paydeal.e-sensei.nl/
# desc:		Class for storing the TransactionResponse

class AcquirerTransactionResponse( object ):
	"""
		Contains all response information for a transaction request
	"""
	def __init__( self ):
		self.acquirerID		= ''
		self.issuerAuthenticationURL = ''
		self.transactionID	= ''
		self.purchaseID		= ''
		self.errorMessage	= False
	
	def getAcquirerID( self ):
		"""
			@return Returns the acquirerID.
		"""
		return self.acquirerID
	
	def setAcquirerID( self, acquirerID ):
		"""
			@param acquirerID The acquirerID to set. ( mandatory)
		"""
		self.acquirerID = acquirerID
	
	def getIssuerAuthenticationURL( self ):
		"""
			@return Returns the issuerAuthenticationURL.
		"""
		return self.issuerAuthenticationURL
	
	def setIssuerAuthenticationURL( self, issuerAuthenticationURL ):
		"""
			@param issuerAuthenticationURL The issuerAuthenticationURL to set.
		"""
		self.issuerAuthenticationURL = issuerAuthenticationURL
	
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
	
	def getPurchaseID( self ):
		"""
			@return Returns the purchaseID.
		"""
		return self.purchaseID
	
	def setPurchaseID( self, purchaseID ):
		"""
			@param purchaseID The purchaseID to set. ( mandatory)
		"""
		self.purchaseID = purchaseID
   
	def IsResponseError( self ):
		return False
