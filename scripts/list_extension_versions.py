"""List the current versions of the DCOR extensions

The output of this script should be written to
dcor_control/resources/compatible_versions.csv.
The idea is to have a trace of compatible DCOR
extensions. This should be done on a regular basis,
but at the least whenever an incompatibility is
introduced.
"""
try:
    from ckan import __version__ as ckan_version
except BaseException:
    ckan_version = "unknown!"

from ckanext import dc_log_view
from ckanext import dc_serve
from ckanext import dc_view
from ckanext import dcor_depot
from ckanext import dcor_schemas
from ckanext import dcor_theme
import dcor_shared


versions = {
    "ckan": ckan_version,
    "ckanext.dc_log_view": dc_log_view.__version__,
    "ckanext.dc_serve": dc_serve.__version__,
    "ckanext.dc_view": dc_view.__version__,
    "ckanext.dcor_depot": dcor_depot.__version__,
    "ckanext.dcor_schemas": dcor_schemas.__version__,
    "ckanext.dcor_theme": dcor_theme.__version__,
    "dcor_shared": dcor_shared.__version__,
    }


min_cell_width = 10

keys = sorted(versions.keys())

key_line = ""
ver_line = ""

for kk in keys:
    cell_width = max(min_cell_width, len(kk) + 2)
    key_line += kk.ljust(cell_width)
    ver_line += versions[kk].ljust(cell_width)

print(key_line)
print(ver_line)
