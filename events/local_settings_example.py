# Dyonisos local settings file

# SECURITY WARNING: Make this unique, and don't share it with anybody.
# Fill it with some random characters and make it long and unique.
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Set this to your favourite mysql database. Default: sqlite
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'events',
#         'USER': 'events',
#         'PASSWORD': '',
#         'HOST': '127.0.0.1',
#         'PORT': '',
#     }
# }

# The STATIC_ROOT is not necessary for testing with 'manage.py runserver'
# STATIC_ROOT = '/usr/share/events/static/'
STATIC_URL = '/static/'

# EMAIL
EMAIL_HOST = 'localhost'
EMAIL_PORT = '25'
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = ''

# Janeus settings
# Uncomment if you have an LDAP server
# JANEUS_SERVER = "ldap://127.0.0.1:389/"
# JANEUS_DN = "cn=readuser, ou=sysUsers, dc=jd, dc=nl"
# JANEUS_PASS = ""
# def JANEUS_CURRENT_SITE(): return 1
# AUTHENTICATION_BACKENDS = ('janeus.backend.JaneusBackend', 'django.contrib.auth.backends.ModelBackend',)

# Key for Mollie
# You need a Mollie account, use the test key for testing
# This is only necessarry for testing paying. If you don't
# have a Mollie account, then don't set prices.
MOLLIE_KEY = ''
