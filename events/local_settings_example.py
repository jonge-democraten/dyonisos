# Dyonisos local settings file

# SECURITY WARNING: Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = []

ADMINS = (
    ('name', 'name@domain.com'),
)

ALLOWED_HOSTS = ['events.jongedemocraten.nl']

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

LANGUAGE_CODE = 'nl_NL'
TIME_ZONE = 'Europe/Amsterdam'

STATIC_ROOT = '/usr/share/events/htdocs/'
STATIC_URL = 'https://events-static.jongedemocraten.nl/'

# Janeus settings

JANEUS_SERVER = "ldap://127.0.0.1:389/"
JANEUS_DN = "cn=readuser, ou=sysUsers, dc=jd, dc=nl"
JANEUS_PASS = ""
JANEUS_AUTH = lambda user, groups: "role-team-ict" in groups or "role-bestuur-landelijk" in groups
from django.db.models import Q
JANEUS_AUTH_PERMISSIONS = lambda user,groups: Q(content_type__app_label='subscribe')
AUTHENTICATION_BACKENDS = ('janeus.backend.JaneusBackend', 'django.contrib.auth.backends.ModelBackend',)


# Dyonisos specific configuration

MOLLIE = { # Mollie config
    'partner_id': 0, # Mollie.nl accountnummer
    'profile_key': '',
    'report_url': 'https://events.jongedemocraten.nl/report/',
    'return_url': 'https://events.jongedemocraten.nl/return/',
    'testmode': 'false'
}
