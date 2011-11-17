#!/usr/bin/env python

# payDEAL - the iDEAL module for Python
# file:		ErrorResponse.py
# author:	Wai Yi Leung <w.y.leung@e-sensei.nl>
# website:	http://paydeal.e-sensei.nl/
# desc:		Class for storing the ErrorResponse

class ErrorResponse( object ):
	"""
		Contains error information.
	"""
	def __init__( self ):
		self.errCode		= ''
		self.errMsg			= ''
		self.consumerMsg	= ''
		self.errorMessage	= True

	def getErrorCode( self ):
		return self.errCode

	def getErrorMessage( self ):
		return self.errMsg

	def getConsumerMessage( self ):
		return self.consumerMsg

	def setErrorCode( self, errCode ):
		self.errCode = errCode

	def setErrorMessage( self, errMsg ):
		self.errMsg = errMsg

	def setConsumerMessage( self, consumerMsg ):
		self.consumerMsg = consumerMsg

	def IsResponseError( self ):
		return True
