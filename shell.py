import code
import logging

import sys, os

APP_ID = None
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_sdk():
  # Try to import the appengine code from the system path.
  try:
    from google.appengine.api import apiproxy_stub_map
  except ImportError, e:
    # Hack to fix reports of import errors on Ubuntu 9.10.
    if 'google' in sys.modules:
      del sys.modules['google']
    # Not on the system path. Build a list of alternative paths where it may be.
    # First look within the project for a local copy, then look for where the Mac
    # OS SDK installs it.
    paths = [os.path.join(PROJECT_DIR, '.google_appengine'),
             os.path.join(PROJECT_DIR, 'google_appengine'),
             '/usr/local/google_appengine']
    # Then if on windows, look for where the Windows SDK installed it.
    for path in os.environ.get('PATH', '').split(';'):
      path = path.rstrip('\\')
      if path.endswith('google_appengine'):
        paths.append(path)
    try:
      from win32com.shell import shell
      from win32com.shell import shellcon
      id_list = shell.SHGetSpecialFolderLocation(
          0, shellcon.CSIDL_PROGRAM_FILES)
      program_files = shell.SHGetPathFromIDList(id_list)
      paths.append(os.path.join(program_files, 'Google',
                                'google_appengine'))
    except ImportError, e:
      # Not windows.
      pass
    # Loop through all possible paths and look for the SDK dir.
    SDK_PATH = None
    for sdk_path in paths:
      if os.path.exists(sdk_path):
        SDK_PATH = os.path.realpath(sdk_path)
        break
    if SDK_PATH is None:
      # The SDK could not be found in any known location.
      sys.stderr.write("The Google App Engine SDK could not be found!\n")
      sys.stderr.write("See README for installation instructions.\n")
      sys.exit(1)
    if SDK_PATH == os.path.join(PROJECT_DIR, 'google_appengine'):
      logging.warn('Loading the SDK from the \'google_appengine\' subdirectory '
                   'is now deprecated!')
      logging.warn('Please move the SDK to a subdirectory named '
                   '\'.google_appengine\' instead.')
      logging.warn('See README for further details.')
    # Add the SDK and the libraries within it to the system path.
    EXTRA_PATHS = [
        SDK_PATH,
        os.path.join(SDK_PATH, 'lib', 'antlr3'),
        os.path.join(SDK_PATH, 'lib', 'django'),
        os.path.join(SDK_PATH, 'lib', 'ipaddr'),
        os.path.join(SDK_PATH, 'lib', 'webob'),
        os.path.join(SDK_PATH, 'lib', 'simplejson'),
        os.path.join(SDK_PATH, 'lib', 'whoosh'),
        os.path.join(SDK_PATH, 'lib', 'yaml', 'lib'),
        os.path.join(SDK_PATH, 'lib', 'fancy_urllib'),
    ]
    # Add SDK paths at the start of sys.path, but after the local directory which
    # was added to the start of sys.path on line 50 above. The local directory
    # must come first to allow the local imports to override the SDK and
    # site-packages directories.
    sys.path = sys.path[0:1] + EXTRA_PATHS + sys.path[1:]

def load_environment():
  """ Loads the appengine environment. """
  global APP_ID
  from google.appengine.api import yaml_errors
  from google.appengine.api import apiproxy_stub_map


  # get the APP_ID
  try:
    from google.appengine.tools import dev_appserver
    appconfig, unused_matcher = dev_appserver.LoadAppConfig(PROJECT_DIR, {})
    APP_ID = appconfig.application
  except (ImportError, yaml_errors.EventListenerYAMLError), e:
    logging.warn("Could not read the Application ID from app.yaml. "
                 "This may break things in unusual ways!")
    # Something went wrong.
    APP_ID = "unknown"


def load_stubs():
  from google.appengine.tools import dev_appserver_main
  args = dev_appserver_main.DEFAULT_ARGS.copy()
  from google.appengine.tools import dev_appserver
  dev_appserver.SetupStubs(APP_ID, **args)

  logging.debug("Loading application '%s'" % (APP_ID))



if __name__ == '__main__':
  load_sdk()
  load_environment()
  load_stubs()
  code.interact('App Engine interactive console', None, locals())

