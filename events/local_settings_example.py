# Dyonisos local settings file

# SECURITY WARNING: Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'events',
        'USER': 'events',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
}

# STATIC_ROOT = '/usr/share/events/static/'
STATIC_URL = '/static/'

# Janeus settings
# Uncomment if you have an LDAP server

# JANEUS_SERVER = "ldap://127.0.0.1:389/"
# JANEUS_DN = "cn=readuser, ou=sysUsers, dc=jd, dc=nl"
# JANEUS_PASS = ""
# AUTHENTICATION_BACKENDS = ('janeus.backend.JaneusBackend', 'django.contrib.auth.backends.ModelBackend',)

# Key for Mollie
# You need a Mollie account, use the test key for testing
MOLLIE_KEY = ''
