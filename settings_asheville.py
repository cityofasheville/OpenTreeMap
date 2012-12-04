import os

GEOSERVER_URL = 'http://72.250.240.58:8081/geoserver/wms?transparent=true'
TILECACHE_URL = 'http://72.250.240.58/tilecache/tilecache.py/'
TILECACHE_LAYER = 'ATM'
GEOSERVER_GEO_LAYER='ashevilletree_gis:selected_trees'
GEOSERVER_GEO_STYLE=""

SITE_LOCATION = 'Asheville'
COMPLETE_ARRAY = ['species','condition','sidewalk_damage','powerline_conflict_potential','canopy_height','canopy_condition','dbh','plot_width','plot_length','plot_type','condition','tree_owner','steward_user_id','steward_name']
#COMPLETE_ARRAY = ['species']
REGION_NAME = 'Asheville'
PENDING_ON = False
MAP_CLICK_RADIUS = .0015 # in decimal degrees

GOOGLE_API_KEY = 'AIzaSyD9gqeiFZINN-TasiLoqCufNRngSxtjNNU'

ADMINS = (
    ('Admin1', 'dmichelson@ashevillenc.gov'),
)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL= 'dmichelson@ashevillenc.gov'
CONTACT_EMAILS = ['dmichelson@ashevillenc.gov']
EMAIL_MANAGERS = False

EMAIL_HOST = 'coa-exchange2k3.asheville.local'
EMAIL_PORT = 25

TILED_SEARCH_RESPONSE = False

# separate instance of tilecache for dynamic selection tiles
CACHE_SEARCH_TILES = True
CACHE_SEARCH_METHOD = 'disk' #'disk'
CACHE_SEARCH_DISK_PATH = os.path.join(os.path.dirname(__file__), 'local_tiles/')
MAPNIK_STYLESHEET = os.path.join(os.path.dirname(__file__), 'mapserver/stylesheet.xml')

CACHE_BACKEND = 'file:///tmp/trees_cache'

# django-registration
REGISTRATION_OPEN = True # defaults to True
ACCOUNT_ACTIVATION_DAYS = 5

DATABASES = {
    'default': {
        'NAME': 'ashevilletrees',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'USER': 'postgres',                      # Not used with sqlite3.
        'PASSWORD': 'pgAdmin11',                  # Not used with sqlite3.
        'HOST': '192.168.0.91',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'


SITE_ID = 1
ROOT_URL = "http://72.250.240.58"
SITE_ROOT = '/OpenTreeMap/'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')
MEDIA_URL = ''
STATIC_URL = '/OpenTreeMap/static/'
ADMIN_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'admin_media/')
ADMIN_MEDIA_PREFIX = '/admin_media/'

STATIC_DATA = os.path.join(os.path.dirname(__file__), 'static/')

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'dudewheresmytrees'


TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates/Asheville'),
    os.path.join(os.path.dirname(__file__), 'templates'),
)


