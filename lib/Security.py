#!/usr/bin/env python

# payDEAL - the iDEAL module for Python
# file:		Security.py
# author:	Wai Yi Leung <w.y.leung@e-sensei.nl>
# website:	http://paydeal.e-sensei.nl/
# desc:		Security handling, decryption and encryption
#			This module requires the M2Crypto package from
#			http://chandlerproject.org/bin/view/Projects/MeTooCrypto

#import OpenSSL.crypto as pki
import base64, sha, md5
import M2Crypto
# Set the following path to your absolute path were you include the conf
SECURE_PATH = '/usr/share/events/jdideal/lib/includes'

class Security( object ):

# 	def createCertFingerprint( self, sFilename ):
# 		""" createCertFingerprint
# 			reads in a certificate file and creates a fingerprint
# 			@param Filename of the certificate
# 			@return fingerprint
# 		"""
# 		try:
# 			pCertFile = open( sFilename,'r' )
# 		except:
# 			return False
# 		else:
# 			sCertContents = pCertFile.read()
# 			pCertFile.close()
# 
# 		self.oCA_KEY = pki.load_certificate( pki.FILETYPE_PEM, sCertContents )
# 
# 		sData = pki.dump_certificate( pki.FILETYPE_PEM, self.oCA_KEY )
# 		sData = sData.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '')
# 		sData = base64.b64decode( sData )
# 		sFingerprint = sha.new( sData ).hexdigest().upper()
# 		del sData
# 		return sFingerprint


	def createCertFingerprint( self, sCertfile ):
		""" createCertFingerprint
			reads in a certificate file and creates a fingerprint
			@param Filename of the certificate
			@return fingerprint
		"""

		oCA = M2Crypto.X509.load_cert( SECURE_PATH+'/'+sCertfile )
		sFingerprint = oCA.get_fingerprint('sha1')
		del oCA
		# fill the fingerprint with zero's upto 40 chars.
		return unicode(sFingerprint.zfill(40))

	def signMessage( self, sPrivKeyfile, sKeyPass, sData ):
		""" signMessage
			function to sign a message
			@param filename of the private key
			@param message to sign
			@return signature
		"""

		oPKey = M2Crypto.EVP.load_key( SECURE_PATH+'/'+sPrivKeyfile, lambda x: str(sKeyPass) )
		oPKey.sign_init()
		oPKey.sign_update( str(sData) )
		signature = oPKey.final()
		del oPKey
		return signature

	def verifyMessage( self, sCertfile, sData, sSignature ):
		""" verifyMessage
			function to verify a message
			@param filename of the public key to decrypt the signature
			@param message to verify
			@param sent signature
			@return signature
		"""
		bOK	= False

		# get public key from certificate
		oCA = M2Crypto.X509.load_cert( SECURE_PATH+'/'+sCertfile )
		oPKey = oCA.get_pubkey()
		oPKey.verify_init()
		oPKey.verify_update( str(sData) )
		bOK = oPKey.verify_final( str(sSignature) )
		del oCA, oPKey
		return bOK

