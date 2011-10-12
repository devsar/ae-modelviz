import os
from os.path import join, dirname, abspath
import inspect
import sys

import shell #depends on https://github.com/devsar/ae-shell/blob/master/shell.py
shell.load_sdk()

from google.appengine.ext import db
from google.appengine.ext.db import polymodel

#COMMENT THIS IF YOU ARE USING THE DJANGO HELPER 
from google.appengine.dist import use_library
use_library('django', '1.2')

#UNCOMMENT THIS IF YOU ARE USING THE DJANGO HELPER
#from appengine_django import InstallAppengineHelperForDjango
#InstallAppengineHelperForDjango('1.2')

## ADD THE PATHS YOU NEED TO IMPORT AS YOUR PROJECT DOES I USUALLY USE:
#PROJECT_DIR = dirname(abspath(__file__))
#sys.path.insert(1, os.path.join(PROJECT_DIR, 'apps'))
#sys.path.insert(1, os.path.join(PROJECT_DIR, 'libs'))

SKIP_METHODS = [
 'all',
 'class_key',
 'class_name',
 'dynamic_properties',
 'delete',
 'entity_type',
 'fields',
 'from_entity',
 'get',
 'get_by_id',
 'get_by_key_name',
 'get_or_insert',
 'gql',
 'has_key',
 'instance_properties',
 'is_saved',
 'key',
 'kind',
 'objects',
 'parent',
 'parent_key',
 'prompt',
 'properties',
 'put',
 'save',
 'to_xml',
]


def process_module(module_name):
  if sys.modules.has_key(module_name):
    module = sys.modules[module_name]
  else:
    module = __import__(module_name, fromlist=[module_name])
  models = map(lambda n: getattr(module,n), dir(module))
  models = filter(lambda m: inspect.isclass(m) and (issubclass(m, db.Model) or issubclass(m, polymodel.PolyModel)), models)
  models = filter(lambda m: inspect.getmodule(m) == module, models)

  graph = {
      'name': '"%s"' % module_name,
      'module_name': module_name.replace(".", "_"),
      'app_name': "%s" % '.'.join(module_name.split('.')[:-1]),
      'models': []
  }

  for appmodel in models:

    model = {
       'module_name': module_name,
       'app_name': appmodel.__module__.replace(".", "_"),
       'name': appmodel.__name__,
       'properties': [],
       'methods': [],
       'references': []
    } 

    if appmodel.mro()[0].__class__.__name__ == 'PolymorphicClass':
      parent = appmodel.mro()[1].__name__
      if parent != 'PolyModel':
        model['parent'] = parent

    #for name, prop in appmodel.properties():
    properties_names = appmodel.properties().keys()

    #get properties
    for name, prop in appmodel.properties().iteritems():
      if name == '_class':
        continue
      prop_type = type(prop).__name__
      if prop_type == 'ReferenceProperty':
        model['references'].append({
                    'target': prop.reference_class.__name__,
                    'type': prop_type,
                    'name': name,
                    'needs_node': True
        })
      else:
        model['properties'].append({
          'name': name,
          'type': prop_type,
          'required': prop.required,
        })

    #get methods
    for name in dir(appmodel):
      if name in SKIP_METHODS or name in properties_names or name.startswith("_"):
        continue
      func = getattr(appmodel, name)
      if inspect.ismethod(func):
        model['methods'].append({
          'name': name,
          'args': ",".join(inspect.getargspec(func).args)
        })

    graph['models'].append(model)

  #del sys.modules[module_name]
  #print "\n".join(sys.modules.keys())
  return graph




def run():
  from google.appengine.ext.webapp.template import Template, Context

  graphs = []
  for module_name in sys.argv[1:]:
    graphs.append(process_module(module_name))

  dot = Template(HEAD_TEMPLATE).render(Context({}))
  for graph in graphs:
    dot += "\n" + Template(BODY_TEMPLATE).render(Context(graph))

  nodes = []
  for graph in graphs:
    nodes.extend([e['name'] for e in graph['models']])

  for graph in graphs:
    # don't draw duplication nodes because of relations
    for model in graph['models']:
      for relation in model['references']:
        if relation['target'] in nodes:
          relation['needs_node'] = False
    dot += "\n" + Template(REFERENCES_TEMPLATE).render(Context(graph))
 
  dot += "\n" + Template(PARENTS_TEMPLATE).render(Context({'graphs': graphs}))

  dot += "}\n"  
  print dot


HEAD_TEMPLATE = """
digraph name {
  fontname = "Helvetica"
  fontsize = 8
  rankdir = "BT"

  node [
    fontname = "Helvetica"
    fontsize = 8
    shape = "plaintext"
  ]
  edge [
    fontname = "Helvetica"
    fontsize = 8
  ]
"""

BODY_TEMPLATE = """
subgraph {{ module_name }} {
  label=<
        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
        <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER"
        ><FONT FACE="Helvetica Bold" COLOR="Black" POINT-SIZE="12"
        >{{ module_name }}</FONT></TD></TR>
        </TABLE>
        >
  color=olivedrab4
  style="rounded"
{% for model in models %}
    {{ model.name }} [label=<
    <TABLE BGCOLOR="palegoldenrod" BORDER="0" CELLBORDER="0" CELLSPACING="0">
     <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4"><FONT FACE="Helvetica Bold" COLOR="white">{{ model.name }}</FONT></TD></TR>
     {% for field in model.properties %}
     <TR>
        <TD ALIGN="LEFT" BORDER="0"><FONT {% if not field.required %}COLOR="#7B7B7B" {% endif %}FACE="Helvetica">{{ field.name }}</FONT></TD>
        <TD ALIGN="LEFT"><FONT {% if not field.required %}COLOR="#7B7B7B" {% endif %}FACE="Helvetica">{{ field.type }}</FONT></TD>
     </TR>
     {% endfor %}
     {% if model.methods %} 
     {% for method in model.methods %}
     <TR>
        <TD BGCOLOR="#F1EFE3" ALIGN="LEFT" BORDER="0"><FONT {% if not field.required %}COLOR="#7B7B7B" {% endif %}FACE="Helvetica">{{ method.name }}</FONT></TD>
        <TD BGCOLOR="#F1EFE3" ALIGN="LEFT"><FONT {% if not field.required %}COLOR="#7B7B7B" {% endif %}FACE="Helvetica">{{ method.args }}</FONT></TD>
     </TR>
     {% endfor %}
     {% endif %}
    </TABLE>
    >, weight={% if model.parent %}2{% else %}1{% endif %}]
{% endfor %}
}
"""

REFERENCES_TEMPLATE = """
{% for model in models %}
  {% for reference in model.references %}
  {% if reference.needs_node %}
  {{ reference.target }} [label=<
      <TABLE BGCOLOR="palegoldenrod" BORDER="0" CELLBORDER="0" CELLSPACING="0">
      <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4"
      ><FONT FACE="Helvetica Bold" COLOR="white"
      >{{ reference.target }}</FONT></TD></TR>
      </TABLE>
      >]
  {% endif %}
  {{ model.name }} -> {{ reference.target }}
  [label="{{ reference.name }}"];
  {% endfor %}
{% endfor %}
"""

PARENTS_TEMPLATE = """
edge [
    arrowhead = "empty"
]
{% for graph in graphs %}
  {% for model in graph.models %}
     {% if model.parent %}
     {{ model.name }} -> {{ model.parent }}
     {% endif %}
  {% endfor %}
{% endfor %}
"""

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_sdk():
  """
    Loads the appengine sdk borrowed from the app engine helper
  """
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


if __name__ == '__main__':
  run()




