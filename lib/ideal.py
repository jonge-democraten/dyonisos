#!/usr/bin/env python
# -*- coding: utf-8 -*-

# payDEAL - the iDEAL module for Python
# file:		ideal.py
# author:	Wai Yi Leung <w.y.leung@e-sensei.nl>
# website:	http://paydeal.e-sensei.nl/
# desc:		The main module file for payDEAL

import pprint, random
import base64, sha, md5
import time, re, urllib2
from AcquirerTransactionResponse import *
from AcquirerStatusResponse import *
from DirectoryResponse import *
from ErrorResponse import *
from Security import *

# Set the following path to your absolute path were you include the conf
SECURE_PATH = '/usr/share/events/jdideal/lib/includes'
"""
	Definition of global constants.
	Can be used but should not be modified by merchant
"""

IDEAL_TX_STATUS_INVALID		= 0x00
IDEAL_TX_STATUS_SUCCESS		= 0x01
IDEAL_TX_STATUS_CANCELLED	= 0x02
IDEAL_TX_STATUS_EXPIRED		= 0x03
IDEAL_TX_STATUS_FAILURE		= 0x04
IDEAL_TX_STATUS_OPEN		= 0x05

ING_ERROR_INVALID_SIGNATURE		= 'ING1000'
ING_ERROR_COULD_NOT_CONNECT		= 'ING1001'
ING_ERROR_PRIVKEY_INVALID		= 'ING1002'
ING_ERROR_COULD_NOT_SIGN		= 'ING1003'
ING_ERROR_CERTIFICATE_INVALID	= 'ING1004'
ING_ERROR_COULD_NOT_VERIFY		= 'ING1005'
ING_ERROR_MISSING_CONFIG		= 'ING1006'
ING_ERROR_PARAMETER				= 'ING1007'
ING_ERROR_INVALID_SIGNCERT		= 'ING1008'

"""
	Definition of private constants
"""

IDEAL_PRV_GENERIC_ERROR			= 'Betalen met IDEAL is nu niet mogelijk. Probeer het later nogmaals of betaal op een andere manier.'
IDEAL_PRV_STATUS_FOUTMELDING	= 'Het resultaat van uw betaling is nog niet bij ons bekend. U kunt desgewenst uw betaling controleren in uw Internetbankieren.'
TRACE_DEBUG						= 'DEBUG'
TRACE_ERROR						= 'ERROR'

class iDEALConnector( object ):
	def __init__( self ):
		self.error = ''

		self.config = self.loadConfig()
		self.verbosity, result = self.getConfiguration( "TRACELEVEL", True, True )
		self.Security = Security()

	def GetIssuerList( self ):
		self.clearError()
		configCheck = self.CheckConfig( self.config )

		if configCheck <> unicode('OK'):
			errorResponse = ErrorResponse()
			errorResponse.setErrorCode('001')
			errorResponse.setErrorMessage('Config error: %s' % configCheck)
			errorResponse.setConsumerMessage('')

			return errorResponse

		# Build up the XML header for this request
		xmlMsg = self.getXMLHeader('DirectoryReq', '', '', '', '')
		if not xmlMsg:
			return False

		xmlMsg += u"</DirectoryReq>\n"

		# Post the XML to the server.
		response = self.PostXMLData( xmlMsg )

		# If the response did not work out, return an ErrorResponse object.
		if not self.parseFromXml( 'errorCode', response ) in ['', False]:
			errorResponse = ErrorResponse()

			errorResponse.setErrorCode(self.parseFromXml( 'errorCode', response ))
			errorResponse.setErrorMessage(self.parseFromXml( 'errorMessage', response ))
			errorResponse.setConsumerMessage(self.parseFromXml( 'consumerMessage', response ))

			return errorResponse

		if self.parseFromXml( 'acquirerID', response ) == '':
			errorResponse = ErrorResponse()

			errorResponse.setErrorCode('ING1001')
			errorResponse.setErrorMessage('DirectoryList service probleem')
			errorResponse.setConsumerMessage('')
				
			return errorResponse

		# Create a new DirectoryResponse object with the required information
		res = DirectoryResponse()
		res.setAcquirerID( self.parseFromXml( 'acquirerID', response ) )
		res.setDirectoryDateTimeStamp( self.parseFromXml( 'directoryDateTimeStamp', response ) )

		# While there are issuers to be read from the stream
		while response.find('<issuerID>' ) is not -1:

			# Read the information for the next issuer.
			issuerID	= self.parseFromXml( 'issuerID', response )
			issuerName	= self.parseFromXml( 'issuerName', response )
			issuerList	= self.parseFromXml( 'issuerList', response )

			# Create a new entry and add it to the list
			issuerEntry = IssuerEntry()
			issuerEntry.setIssuerID( issuerID )
			issuerEntry.setIssuerName( issuerName )
			issuerEntry.setIssuerListType( issuerList )
			res.addIssuer( issuerEntry )
				
			# Find the next issuer.
			response = response[response.find('</issuerList>')+13: ]

		return res


	def RequestTransaction( self, issuerId, purchaseId, amount, description, entranceCode, optExpirationPeriod='', optMerchantReturnURL='' ):
		"""
			This function submits a transaction request to the server.

			@param string $issuerId			The issuer Id to send the request to
			@param string $purchaseId		The purchase Id that the merchant generates
			@param integer $amount			The amount in cents for the purchase
			@param string $description		The description of the transaction
			@param string $entranceCode		The entrance code for the visitor of the merchant site. Determined by merchant
			@param string $optExpirationPeriod		Expiration period in specific format. See reference guide. Can be configured in config.
			@param string $optMerchantReturnURL		The return URL (optional) for the visitor. Optional. Can be configured in config.
			@return An instance of AcquirerTransactionResponse or "false" on failure.
		"""
		self.clearError()
		configCheck = self.CheckConfig( self.config )

		if configCheck <> unicode('OK'):
			self.setError( ING_ERROR_MISSING_CONFIG, 'Config error: %s' % configCheck, IDEAL_PRV_GENERIC_ERROR )
			return self.getError()

		if not self.verifyNotNull( issuerId, 'issuerId' ) or \
			not self.verifyNotNull( purchaseId, 'purchaseId' ) or \
			not self.verifyNotNull( amount, 'amount' ) or \
			not self.verifyNotNull( description, 'description' ) or \
			not self.verifyNotNull( entranceCode, 'entranceCode' ):
			errorResponse = self.getError()
			return errorResponse

		# check amount length
		amountOK = self.LengthCheck( 'Amount', amount, 12 )
		if amountOK != "ok":
			return self.getError()

		# check for diacritical characters
		amountOK = self.CheckDiacritical( 'Amount', amount )
		if amountOK != "ok":
			return self.getError()

		# check entrancecode length
		entranceCodeOK = self.LengthCheck( 'Entrancecode', entranceCode, 40 )
		if entranceCodeOK != "ok":
			return self.getError()
		# check for diacritical characters
		entranceCodeOK = self.CheckDiacritical( 'Entrancecode', entranceCode )
		if entranceCodeOK != "ok":
			return self.getError()

		# check purchaseid length
		purchaseIDOK = self.LengthCheck( 'PurchaseID', purchaseId, 16 )
		if purchaseIDOK != "ok":
			return self.getError()
		# check for diacritical characters
		purchaseIDOK = self.CheckDiacritical( 'PurchaseID', purchaseId )
		if purchaseIDOK != "ok":
			return self.getError()

		# According to the specification, these values should be hardcoded.
		currency = 'EUR'
		language = 'nl'

		# Retrieve these values from the configuration file.
		cfgExpirationPeriod, result1 = self.getConfiguration( 'EXPIRATIONPERIOD', True )
		cfgMerchantReturnURL, result2 = self.getConfiguration( 'MERCHANTRETURNURL', True )

		if len( optExpirationPeriod ):
			# If a (valid?) optional setting was specified for the expiration period, use it.
			expirationPeriod = optExpirationPeriod
		else:
			expirationPeriod = cfgExpirationPeriod

		if len( optMerchantReturnURL ):
			# If a (valid?) optional setting was specified for the merchantReturnURL, use it.
			merchantReturnURL = optMerchantReturnURL
		else:
			merchantReturnURL = cfgMerchantReturnURL

		if not self.verifyNotNull( expirationPeriod, 'expirationPeriod' ) or \
			not self.verifyNotNull( merchantReturnURL, 'merchantReturnURL' ):
			return False

		# Build the XML header for the transaction request
		xmlMsg = self.getXMLHeader(
        	'AcquirerTrxReq', 
			issuerId,
			"<Issuer>\n<issuerID>%s</issuerID>\n</Issuer>\n" % issuerId,
			"%s%s%s%s%s%s%s" % (merchantReturnURL, purchaseId, amount, currency, language, description, entranceCode),
			"<merchantReturnURL>%s</merchantReturnURL>\n" % merchantReturnURL )
			
		if xmlMsg in [False, '']:
			return False

		# Add transaction information to the request.
		xmlMsg += "<Transaction>\n<purchaseID>%s</purchaseID>\n" % purchaseId;
		xmlMsg += "<amount>%s</amount>\n" % amount;
		xmlMsg += "<currency>%s</currency>\n" % currency;
		xmlMsg += "<expirationPeriod>%s</expirationPeriod>\n" % expirationPeriod;
		xmlMsg += "<language>%s</language>\n" % language;
		xmlMsg += "<description>%s</description>\n" % description;
		xmlMsg += "<entranceCode>%s</entranceCode>\n" % entranceCode;
		xmlMsg += "</Transaction>\n";
		xmlMsg += "</AcquirerTrxReq>\n";

		# Post the request to the server.
		response = self.PostXMLData( xmlMsg )

		# If the response did not work out, return an ErrorResponse object.
		if not self.parseFromXml( 'errorCode', response ) in ['', False]:
			errorResponse = ErrorResponse()

			errorResponse.setErrorCode(self.parseFromXml( 'errorCode', response ))
			errorResponse.setErrorMessage(self.parseFromXml( 'errorMessage', response ))
			errorResponse.setConsumerMessage(self.parseFromXml( 'consumerMessage', response ))

			return errorResponse

		if self.parseFromXml( 'acquirerID', response ) in ['', False]:
			errorResponse = ErrorResponse()

			errorResponse.setErrorCode('ING1001')
			errorResponse.setErrorMessage('Transactie mislukt (aquirer side)')
			errorResponse.setConsumerMessage('')
				
			return errorResponse

		html_decode_table = {
			"&amp;": "&",
			"&quot;": '"',
			"&apos;": "'",
			"&gt;": ">",
			"&lt;": "<",
			}
		
		def html_decode(text):
			"""Produce entities within text."""
			L=[]
			for c in text:
				L.append(html_decode_table.get(c,c))
			return "".join(L)

		# Build the transaction response object and pass in the data.
		res = AcquirerTransactionResponse()
		res.setAcquirerID( self.parseFromXml( 'acquirerID', response ) )
		res.setIssuerAuthenticationURL( html_decode( self.parseFromXml( 'issuerAuthenticationURL', response ) ) )
		res.setTransactionID( self.parseFromXml( 'transactionID', response ) )
		res.setPurchaseID( self.parseFromXml( 'purchaseID', response ) )

		if not res:
			return response
		
		return res


	def RequestTransactionStatus( self, transactionId ):
		""" RequestTransactionStatus
			This public function makes a transaction status request

			@param string $transactionId	The transaction ID to query. (as returned from the TX request)
			@return An instance of AcquirerStatusResponse or FALSE on failure.
		"""
		self.clearError()
		configCheck = self.CheckConfig( self.config )

		if configCheck <> unicode('OK'):
			errorResponse = ErrorResponse()
			errorResponse.setErrorCode('001')
			errorResponse.setErrorMessage('Config error: %s' % configCheck)
			errorResponse.setConsumerMessage('')

			return errorResponse

		# check TransactionId length
		if not self.LengthCheck( 'TransactionID', transactionId, 16 ).lower() == 'ok'.lower():
			return self.getError()
		if not self.verifyNotNull( transactionId, 'transactionId'):
			return self.getError()

		# Build the status request XML.
		xmlMsg = self.getXMLHeader('AcquirerStatusReq', '', '', transactionId, '')
		if not xmlMsg:
			return False

		# Add transaction information.
		xmlMsg += u"<Transaction>\n<transactionID>%s</transactionID></Transaction>\n" % transactionId
		xmlMsg += u"</AcquirerStatusReq>\n"

		# Post the request to the server.
		response = self.PostXMLData( xmlMsg )
		# If the response did not work out, return an ErrorResponse object.
		if not self.parseFromXml( 'errorCode', response ) in ['', False]:
			errorResponse = ErrorResponse()

			errorResponse.setErrorCode(self.parseFromXml( 'errorCode', response ))
			errorResponse.setErrorMessage(self.parseFromXml( 'errorMessage', response ))
			errorResponse.setConsumerMessage(self.parseFromXml( 'consumerMessage', response ))

			return errorResponse

		if self.parseFromXml( 'acquirerID', response ) in ['', False]:
			errorResponse = ErrorResponse()

			errorResponse.setErrorCode('ING1001')
			errorResponse.setErrorMessage('Status lookup mislukt (aquirer side)')
			errorResponse.setConsumerMessage('')
				
			return errorResponse

		# Build the status response object and pass the data into it.
		res = AcquirerStatusResponse()
		creationTime = self.parseFromXml( 'createDateTimeStamp', response )
		res.setAcquirerID( self.parseFromXml( 'acquirerID', response ) )
		res.setConsumerName( self.parseFromXml( 'consumerName', response ) )
		res.setConsumerAccountNumber( self.parseFromXml( 'consumerAccountNumber', response ) )
		res.setConsumerCity( self.parseFromXml( 'consumerCity', response ) )
		res.setTransactionID( self.parseFromXml( 'transactionID', response ) )
		
		# The initial status is INVALID, so that future modifications to
		# this or remote code will yield alarming conditions.
		res.setStatus( IDEAL_TX_STATUS_INVALID )
		status = self.parseFromXml( 'status', response )

		# Determine status identifier (case-insensitive).
		dStatus = {
			'Success': IDEAL_TX_STATUS_SUCCESS,
			'Cancelled': IDEAL_TX_STATUS_CANCELLED,
			'Expired': IDEAL_TX_STATUS_EXPIRED,
			'Failure': IDEAL_TX_STATUS_FAILURE,
			'Open': IDEAL_TX_STATUS_OPEN
		}

		for statuscode in dStatus.keys():
			if status.lower() == statuscode.lower():
				res.setStatus( dStatus[ statuscode ] )
		# The verification of the response starts here.
		# The message as per the reference guide instructions.
		consumerAccountNumber = res.getConsumerAccountNumber()
		if consumerAccountNumber == False:
			consumerAccountNumber = ''
		message = self.strip( '%s%s%s%s' % ( creationTime, res.getTransactionID(), status, consumerAccountNumber ) )
		# The signature value in the response contains the signed hash
		# (signed by the signing key on the server)
		signature64 = self.parseFromXml( 'signatureValue', response )

		# The signed hash is base64 encoded and inserted into the XML as such
		sig = base64.b64decode( signature64 )

		# The fingerprint is used as the identifier of the public key certificate.
		# It is sent as part of the response XML.
		fingerprint = self.parseFromXml( 'fingerprint', response )

		# The merchant should have the public certificate stored locally.
		certfile = self.getCertificateFileName( fingerprint )
		if certfile in ['', False]:
			return False

		# Verify the message signature
		valid = self.Security.verifyMessage( certfile, str(message), str(sig) )
		if not valid:
			return False

		if not res:
			return response
		
		return res

	def getError( self ):
		""" getError
			This public function returns the ErrorResponse object or "" if it does not exist.
			@return ErrorResponse object or an emptry string "".
		"""
		return self.error

	#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-#
	#                           private functions                                   #
	#-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-#

	def log( self, desiredVerbosity, message ):
		""" log
			Logs a message to the file.
			@param string desiredVerbosity	The desired verbosity of the message
			@param string message			The message to log
		"""
		# Check if the log file is set. If not set, don't log.
		if 'LOGFILE' not in self.config or self.config['LOGFILE'] == '':
			return

		if desiredVerbosity not in self.verbosity:
			# The desired verbosity is not listed in the configuration
			return

		# Open the log file in 'append' mode.
		pFile = open( SECURE_PATH+'/'+self.config['LOGFILE'], 'a' )
		pFile.write( "%s: %s: %s\r\n" % ( self.getCurrentDateTime(), desiredVerbosity.upper(), message ) )
		pFile.close()

	def setError( self, errCode, errMsg, consumerMsg ):
		""" setError
			Creates a new ErrorResponse object and populates it with the arguments

			@param unknown_type errCode		The error code to return. This is either a code from the platform or an internal code.
			@param unknown_type errMsg		The error message. This is not meant for display to the consumer.
			@param unknown_type consumerMsg	The consumer message. The error message to be shown to the user.
		"""
		self.error = ErrorResponse()
		self.error.setErrorCode( errCode )
		self.error.setErrorMessage( errCode )
		if len( consumerMsg ):
			self.error.setConsumerMessage( consumerMsg )
		else:
			self.error.setConsumerMessage( IDEAL_PRV_GENERIC_ERRORMESSAGE )

	def clearError( self ):
		""" clearError
			Clears the error conditions.
		"""
		#iDEALConnector_error = 0
		#iDEALConnector_errstr = ''
		self.error = ''

	def getXMLHeader( self, msgType, firstCustomIdInsert, firstCustomFragment, secondCustomIdInsert, secondCustomFragment ):
		""" getXMLHeader
			Builds up the XML message header.

			@param string msgType				The type of message to construct.
			@param string firstCustomIdInsert	The identifier value(s) to prepend to the hash ID.
			@param string firstCustomFragment	The fragment to insert in the header before the general part.
			@param string secondCustomIdInsert	The identifier value(s) to append to the hash ID.
			@param string secondCustomFragment	The XML fragment to append to the header after the general part.
			@return string
		"""
		# Determine the (string) timestamp for the header and hash id.
		timestamp = self.getCurrentDateTime()

		# Merchant ID and sub ID come from the configuration file.
		merchantId, result = self.getConfiguration( "MERCHANTID", False )
		subId, result = self.getConfiguration( "SUBID", False )

		if not result:
			return False

		# Build the hash ID
		message = self.strip( "%s%s%s%s%s" % ( str(timestamp), str(firstCustomIdInsert), str(merchantId), str(subId), str(secondCustomIdInsert) ) )
		# Create the certificate fingerprint used to sign the message. This is passed in to identify
		# the public key of the merchant and is used for authentication and integrity checks.
		privateCert, result = self.getConfiguration( "PRIVATECERT", False )
		if not result:
			return False

		token = self.Security.createCertFingerprint( privateCert )

		if not token:
			return False

		# Calculate the base-64'd hash of the hashId and store it in tokenCode.
		tokenCode = self.calculateHash( message )

		if not tokenCode:
			return False

		# Start building the header.
#		xmlHeader = u'<?xml version="1.0" encoding="UTF-8"?>\n<%s xmlns="http://www.idealdesk.com/Message" version="1.1.0">\n<createDateTimeStamp>%s</createDateTimeStamp>\n' % ( msgType, timestamp )

		xmlHeader = u"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
		xmlHeader += u"<" + msgType + " xmlns=\"http://www.idealdesk.com/Message\" version=\"1.1.0\">\n"
		xmlHeader += u"<createDateTimeStamp>" + timestamp + "</createDateTimeStamp>\n"

		if len( firstCustomFragment ):
			# If there is a custom fragment to prepend, insert it here.
			xmlHeader += unicode(firstCustomFragment + "\n")

		# The general parts of the header
#		xmlHeader += u'<Merchant>\n<merchantID>%s</merchantID>\n<subID>%s</subID>\n<authentication>SHA1_RSA</authentication>\n<token>%s</token>\n<tokenCode>%s</tokenCode>\n' % ( self.encode_html( merchantId ), subId, token, tokenCode )

		xmlHeader += u"<Merchant>\n"
		xmlHeader += u"<merchantID>" +self.encode_html( merchantId )+ "</merchantID>\n"
		xmlHeader += u"<subID>" +subId+ "</subID>\n"
		xmlHeader += u"<authentication>SHA1_RSA</authentication>\n"
		xmlHeader += u"<token>" +unicode(token)+ "</token>\n"
		xmlHeader += u"<tokenCode>" +unicode(tokenCode)+ "</tokenCode>\n"

		if len( secondCustomFragment ):
			# If there is a fragment to append, append it here.
			xmlHeader += secondCustomFragment
		# Close the header and return it.
		xmlHeader += u'</Merchant>\n'

		return xmlHeader

	def strip( self, message ):
		""" strip
			Strips whitespace from a string.

			@param string $message	The string to strip.
			@return string			The stripped string.
		"""
		return message.replace(" ", "").replace("\t", "").replace("\n", "")

	def encode_html( self, text):
		""" encode_html
			Encodes HTML entity codes to characters

			@param string text	The text to encode
			@return string 		The encoded text
		"""
		html_escape_table = {
			"&": "&amp;",
			'"': "&quot;",
			"'": "&apos;",
			">": "&gt;",
			"<": "&lt;",
			}
		
		def html_escape(text):
			"""Produce entities within text."""
			L=[]
			for c in text:
				L.append(html_escape_table.get(c,c))
			return "".join(L)

		return html_escape( text )
#		return htmlspecialchars(strtr($text, $trans), ENT_QUOTES)

	def getCurrentDateTime( self ):
		""" getCurrentDateTime
			Gets current date and time.

			@return string	Current date and time.
		"""
		ts = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
		return ts

	def loadConfig( self ):
		""" loadConfig
			Loads the configuration for the MPI interface

			@return array().  An array of the configuration elements
		"""
		dConfData = {}
		
		try:
			# Check if the file exists and read until the end.
			pFile = open( SECURE_PATH + '/config.conf', 'r' )
		except:
			return dConfData
		else:
			dFileBuffer = pFile.readlines()
			pFile.close()
		
		for sLine in dFileBuffer:
			# filter out the commented lines
			if sLine.startswith('#'):
				continue
			dConf = sLine.split('=')
			if len(dConf) == 2: # let's say: having configname and value
				dConfData[ dConf[0].strip().upper() ] = dConf[1].strip()

		return dConfData

	def CheckConfig( self, dConfData ):
		""" CheckConfig

			Checks if the Configuration is set correctly. If an option is not set correctly, it will return an error. This has
			to be checked in the begin of every function that needs these settings and if an error occurs, it must rethrown
			to show it to the user.

			@return string	Error message when configsetting is missing, if no errors occur, ok is thrown back
		"""
		if dConfData['MERCHANTID'] == '':
			return u'MERCHANTID is missing'
		elif len( dConfData['MERCHANTID'] ) > 9:
			return u'MERCHANTID too long!'
		elif dConfData['SUBID'] == '':
			return u'SUBID is missing'
		elif len( dConfData['SUBID'] ) > 6:
			return u'SUBID too long!'
		elif dConfData['ACQUIRERURL'] == '':
			return u'ACQUIRERURL is missing'
		elif dConfData['MERCHANTRETURNURL'] == '':
			return u'MERCHANTRETURNURL is missing'
		elif len( dConfData['MERCHANTRETURNURL'] ) > 512:
			return u'MERCHANTRETURNURL too long!'
		elif dConfData['EXPIRATIONPERIOD'] == '':
			return u'EXPIRATIONPERIOD is missing'
		else:
			return unicode('OK')

	def getConfiguration( self, name, allowMissing, result=False ):
		""" getConfiguration
			Safely get a configuration item.
			Returns the value when name was found, otherwise an emptry string ("").
			If "allowMissing" is set to true, it does not generate an error.

			@param string	name		The name of the configuration item.
			@param boolean	allowMissing	
			@param boolean	result		Not used, built-in for inter-api compatibility
			@return tupple	(The value as specified in the configuration file, boolean result)
		"""
		bResult = ( name in self.config.keys() ) & ( len( self.config.get( name, '') ) > 0 )
		if not bResult and not allowMissing:
			self.log( TRACE_ERROR, 'The configuration item %s is not configured in the configuraton file.' % name )
			self.setError( ING_ERROR_MISSING_CONFIG, 'Missing configuration: %s' % name, IDEAL_PRV_GENERIC_ERROR )
		return ( self.config.get( name, '' ), bResult )

	def calculateHash( self, message ):
		""" calculateHash
			Calculates the hash of a piece and encodes it with base64.

			@param string message	The message to sign.
			@return string			The signature of the message in base64.
		"""
		# Find keys and sign the message
		priv_key, result = self.getConfiguration( 'PRIVATEKEY', False )
		priv_keypass, result = self.getConfiguration( 'PRIVATEKEYPASS', False )

		tokenCode = self.Security.signMessage( priv_key, priv_keypass, message )
		if not result:
			return False
		
		# encode the signature with base64
		tokenCode = base64.b64encode( tokenCode )
		return tokenCode

	def getCertificateFileName( self, fingerprint ):
		"""
			Gets a valid certificate file name based on the certificate fingerprint.
			Uses configuration items in the config file, which are incremented when new
			security certificates are issued:
			certificate0=ideal1.crt
			certificate1=ideal2.crt
			etc...

			@param string $fingerprint	A hexadecimal representation of a certificate's fingerprint
			@return string	The filename containing the certificate corresponding to the fingerprint
		"""
		# Check if the configuration file contains such an item
		for configValue in self.config.keys():
			if configValue.startswith('CERTIFICATE'):
				certFilename = self.config[ configValue ]
			else:
				continue

			# Generate a fingerprint from the certificate in the file.
			buff = self.Security.createCertFingerprint( certFilename )
			if buff == False:
				# Could not create fingerprint from configured certificate.
				return False

			# Check if the fingerprint is equal to the desired one.
			if fingerprint == buff:
				return certFilename

		self.log( TRACE_ERROR, 'Could not find certificate with fingerprint %s' % fingerprint )
		self.setError( ING_ERROR_COULD_NOT_VERIFY, 'Could not verify message', IDEAL_PRV_GENERIC_ERROR )

		# By default, report no success.
		return False

	def PostXMLData( self, message ):
		""" PostXMLData
			Posts XML data to the server or proxy.

			@param string message	The message to post.
			@return string			The response of the server.
		"""
		sProxy, result = self.getConfiguration( 'PROXY', True )
		if sProxy == '':
			acquirerUrl, result = self.getConfiguration( 'ACQUIRERURL', False )

			if not result:
				return False
			# if Proxy configuration does not exist
			return self.PostToHost( acquirerUrl, message )

		proxyUrl, result = self.getConfiguration( 'PROXYACQURL', False )

		if not result:
			return False
		# if proxy is specified
		return self.PostToHostProxy( sProxy, proxyUrl, message )

	def PostToHost( self, sUrl, sDataToSend ):
		""" PostToHost
			Posts a message to the host.

			@param string sUrl	The URL to send the message to.
			@param string sDataToSend	The data to send
			@return string	The response from the server.
		"""
		# Decompose the URL into specific parts.
		sHost, sPort, sPath = re.findall('([\w]+://[\w\d\.-]+):([\d]+)([\w/]+)', sUrl, re.I)[0]

		# Log the request
		self.log( TRACE_DEBUG, 'sending to %s:%s%s: %s' % ( sHost, sPort, sPath, sDataToSend ) )
		return self.PostToServer( sHost, sPort, sPath, sDataToSend )

	def PostToProxy( self, sProxy, sUrl, sDataToSend ):
		""" PostToProxy
			Posts to a proxy, which is slightly different

			@param string sProxy		The proxy to post to
			@param string sUrl			The URL the proxy should post to.
			@param string sDataToSend	The data to send
			@return string	The response
		"""
		# Decompose the proxyURL into specific parts.
		sHost, sPort = re.findall('([\w]+://[\w\d\.-]+):([\d]+)', sProxy, re.I)[0]

		# Log the request
		self.log( TRACE_DEBUG, 'sending through proxy %s:%s: %s' % ( sHost, sPort, sDataToSend ) )

		# Post to the proxy
		return self.PostToServer( sHost, sPort, sUrl, sDataToSend )

	def PostToServer( self, sHost, sPort, sPath, sDataToSend ):
		"""
			Posts to the server and interprets the result

			@param string sHost		The host to post to
			@param string sPort		The port to use
			@param string sPath		The application path on the remote server
			@param string sDataToSend	The data to send
			@return string	The response of the remote server.
		"""
		sRes = ''
		
		# The connection timeout for the remote server
		timeout, result = self.getConfiguration( 'ACQUIRERTIMEOUT', False )
		if not result:
			return False

		# Open connection and report problems in custom error handler.
		

	def PostToServer( self, sHost, sPort, sPath, sDataToSend ):
		""" PostToServer
			Posts to the server and interprets the result

			@param string $host		The host to post to
			@param string $port		The port to use
			@param string $path		The application path on the remote server
			@param string $data_to_send	The data to send
			@return string	The response of the remote server.
		"""
		sHost = sHost.replace('ssl://', 'https://') # urllib2 doesn't like the ssl:// prefix
		sURL = '%s:%s%s' % ( sHost, sPort, sPath )
		# get the connection timeout (config) for the remote server
		timeout, result = self.getConfiguration( 'ACQUIRERTIMEOUT', False )
		if not result:
			return False

		# open the connection and report problems in custom error handler.
		req = urllib2.Request(url=sURL, data=sDataToSend)
		try:
			f = urllib2.urlopen(req)
		except URLError, e:
			# An error occurred when trying to connect to the server.
			self.log( TRACE_ERROR, "Could not connect to: [%s:%s%s]" % ( sHost, sPort, sPath ) )
			self.setError( ING_ERROR_COULD_NOT_CONNECT, "Could not connect to remote server", IDEAL_PRV_GENERIC_ERROR )
			return False
		else:
			sRes = f.read()
			self.log( TRACE_DEBUG, "receiving from %s:%s%s: %s" % ( sHost, sPort, sPath, sRes ) )

			if self.parseFromXml( 'ErrorRes', sRes ):
				self.setError(
					self.parseFromXml( 'errorCode', sRes ),
					self.parseFromXml( 'errorMessage', sRes ),
					self.parseFromXml( 'consumerMessage', sRes ))

				return self.getError()
			
			# return the (textual) response
			return sRes

	def parseFromXml( self, sKey, sXML ):
		""" parseFromXml
			Function to parse XML

			@param string $key	The XML tag to look for.
			@param string $xml	The XML string to look into.
			@return string	The value (PCDATA) inbetween the tag.
		"""
		iBegin = 0
		iEnd = 0
		sXML = sXML.decode('utf8')
		iBegin = sXML.find( '<%s>' % sKey )
		if iBegin == -1:
			return False
		
		iBegin += len( sKey ) + 2 # begin after the tag
		iEnd = sXML.find( '</%s>' % sKey )
		if iEnd == -1:
			return False
		
		sResult = sXML[ iBegin : iEnd ].replace( '&amp;', '&' )
		return unicode(sResult)

	def verifyNotNull( self, sParamValue, sParamName ):
		""" verifyNotNull
			Verifies if the parameter is not empty.

			@param string $parameter
			@param string $paramName
			@return boolean
		"""
		if not len( str( sParamValue ) ) or not len( str( sParamName ) ):
			self.log( TRACE_ERROR, 'The parameter [%s] should have a value.' % sParamName )
			self.setError( ING_ERROR_PARAMETER, 'Empty parameter not allowed: %s' % sParamName, IDEAL_PRV_GENERIC_ERROR )
			return False
		return True

	def LengthCheck( self, sCheckName, sCheckVariable, iCheckLength ):
		""" LengthCheck
			Verifies if the parameter is not too long.

			@param string $checkName
			@param string $checkVariable
			@param string $checkLength

			@return ErrorResponse object when failed, string when succeeded
		"""
		if len( str( sCheckVariable ) ) > int( iCheckLength ):
			self.setError( ING_ERROR_PARAMETER, '%s too long' % sCheckName, IDEAL_PRV_GENERIC_ERROR )
			return 'NotOk'
		return 'ok'

	def CheckDiacritical( self, sCheckName, sCheckVariable ):
		""" CheckDiacritical
			Checks if the inserted variable (sCheckVariable) contains diacritical characters.
			If so, it will return an ErrorResponse object. If not, the string "ok" is returned.

			@param string $checkName
			@param string $checkVariable

			@return ErrorResponse object when failed, string when succeeded
		"""
		pattern = "[áàäãâåæêéèëçìíïîñóòôõöøùúüûýÿ]+"
		match = re.search( pattern, str( sCheckVariable ), re.I )
		if match is not None:
			self.setError( ING_ERROR_PARAMETER, "%s contains diacritical or non-permitted character(s)" % sCheckName, IDEAL_PRV_GENERIC_ERROR )
			return 'NotOk'
		return 'ok'

