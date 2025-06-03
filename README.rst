dcor_control
============


.. list-table:: DCOR development status matrix
   :header-rows: 1

   * - Name
     - Issues
     - Release
     - CI
     - Coverage
   * - `Ansible for DCOR <https://github.com/DCOR-dev/ansible-for-dcor/>`__
     - |ansible issu|
     - |not applicable|
     - |not applicable|
     - |not applicable|
   * - `ckanext-dc_log_view <https://github.com/DCOR-dev/ckanext-dc_log_view/>`__
     - |ckanext-dc_log_view issu|
     - |ckanext-dc_log_view pypi|
     - |ckanext-dc_log_view actn|
     - |ckanext-dc_log_view cvrg|
   * - `ckanext-dc_serve <https://github.com/DCOR-dev/ckanext-dc_serve/>`__
     - |ckanext-dc_serve issu|
     - |ckanext-dc_serve pypi|
     - |ckanext-dc_serve actn|
     - |ckanext-dc_serve cvrg|
   * - `ckanext-dc_view <https://github.com/DCOR-dev/ckanext-dc_view/>`__
     - |ckanext-dc_view issu|
     - |ckanext-dc_view pypi|
     - |ckanext-dc_view actn|
     - |ckanext-dc_view cvrg|
   * - `ckanext-dcor_depot <https://github.com/DCOR-dev/ckanext-dcor_depot/>`__
     - |ckanext-dcor_depot issu|
     - |ckanext-dcor_depot pypi|
     - |ckanext-dcor_depot actn|
     - |ckanext-dcor_depot cvrg|
   * - `ckanext-dcor_schemas <https://github.com/DCOR-dev/ckanext-dcor_schemas/>`__
     - |ckanext-dcor_schemas issu|
     - |ckanext-dcor_schemas pypi|
     - |ckanext-dcor_schemas actn|
     - |ckanext-dcor_schemas cvrg|
   * - `ckanext-dcor_theme <https://github.com/DCOR-dev/ckanext-dcor_theme/>`__
     - |ckanext-dcor_theme issu|
     - |ckanext-dcor_theme pypi|
     - |ckanext-dcor_theme actn|
     - |ckanext-dcor_theme cvrg|
   * - `dcor-remote-tests <https://github.com/DCOR-dev/dcor-remote-tests/>`__
     - |dcor-remote-tests issu|
     - |not applicable|
     - |dcor-remote-tests actn|
     - |not applicable|
   * - `dcor_control <https://github.com/DCOR-dev/dcor_control/>`__
     - |dcor_control issu|
     - |dcor_control pypi|
     - |dcor_control actn|
     - |dcor_control cvrg|
   * - `dcor_shared <https://github.com/DCOR-dev/dcor_shared/>`__
     - |dcor_shared issu|
     - |dcor_shared pypi|
     - |dcor_shared actn|
     - |dcor_shared cvrg|
   * - `DCOR-Aid <https://github.com/DCOR-dev/DCOR-Aid/>`__
     - |DCOR-Aid issu|
     - |DCOR-Aid pypi|
     - |DCOR-Aid actn|
     - |DCOR-Aid cvrg|
   * - User help requests
     - |user help issues|
     - |not applicable|
     - |not applicable|
     - |not applicable|

This is partly a meta package and partly a control/configuration
package for the DCOR extensions in CKAN.


Installation
------------
See the
`official instructions
<https://dc.readthedocs.io/en/latest/sec_self_hosting/installation.html#dcor-extensions>`_
for more information.


Testing
-------
Testing is implemented via GitHub Actions. You may also set up a local
docker container with CKAN and MinIO. Take a look at the GitHub Actions
workflow for more information.

.. |not applicable|
   image:: https://img.shields.io/badge/not%20applicable-888888
   :class: no-scaled-link

.. |ansible issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/ansible-for-dcor.svg
   :target: https://github.com/DCOR-dev/ansible-for-dcor/issues

.. |ckanext-dc_log_view issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/ckanext-dc_log_view.svg
   :target: https://github.com/DCOR-dev/ckanext-dc_log_view/issues
.. |ckanext-dc_log_view pypi|
   image:: https://img.shields.io/pypi/v/ckanext-dc_log_view.svg
   :target: https://pypi.python.org/pypi/ckanext-dc_log_view
.. |ckanext-dc_log_view actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/ckanext-dc_log_view/check.yml
   :target: https://github.com/DCOR-dev/ckanext-dc_log_view/actions/workflows/check.yml
.. |ckanext-dc_log_view cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dc_log_view
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dc_log_view

.. |ckanext-dc_serve issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/ckanext-dc_serve.svg
   :target: https://github.com/DCOR-dev/ckanext-dc_serve/issues
.. |ckanext-dc_serve pypi|
   image:: https://img.shields.io/pypi/v/ckanext-dc_serve.svg
   :target: https://pypi.python.org/pypi/ckanext-dc_serve
.. |ckanext-dc_serve actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/ckanext-dc_serve/check.yml
   :target: https://github.com/DCOR-dev/ckanext-dc_serve/actions/workflows/check.yml
.. |ckanext-dc_serve cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dc_serve
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dc_serve

.. |ckanext-dc_view issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/ckanext-dc_view.svg
   :target: https://github.com/DCOR-dev/ckanext-dc_view/issues
.. |ckanext-dc_view pypi|
   image:: https://img.shields.io/pypi/v/ckanext-dc_view.svg
   :target: https://pypi.python.org/pypi/ckanext-dc_view
.. |ckanext-dc_view actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/ckanext-dc_view/check.yml
   :target: https://github.com/DCOR-dev/ckanext-dc_view/actions/workflows/check.yml
.. |ckanext-dc_view cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dc_view
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dc_view

.. |ckanext-dcor_depot issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/ckanext-dcor_depot.svg
   :target: https://github.com/DCOR-dev/ckanext-dcor_depot/issues
.. |ckanext-dcor_depot pypi|
   image:: https://img.shields.io/pypi/v/ckanext-dcor_depot.svg
   :target: https://pypi.python.org/pypi/ckanext-dcor_depot
.. |ckanext-dcor_depot actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/ckanext-dcor_depot/check.yml
   :target: https://github.com/DCOR-dev/ckanext-dcor_depot/actions/workflows/check.yml
.. |ckanext-dcor_depot cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dcor_depot
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dcor_depot

.. |ckanext-dcor_schemas issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/ckanext-dcor_schemas.svg
   :target: https://github.com/DCOR-dev/ckanext-dcor_schemas/issues
.. |ckanext-dcor_schemas pypi|
   image:: https://img.shields.io/pypi/v/ckanext-dcor_schemas.svg
   :target: https://pypi.python.org/pypi/ckanext-dcor_schemas
.. |ckanext-dcor_schemas actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/ckanext-dcor_schemas/check.yml
   :target: https://github.com/DCOR-dev/ckanext-dcor_schemas/actions/workflows/check.yml
.. |ckanext-dcor_schemas cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dcor_schemas
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dcor_schemas

.. |ckanext-dcor_theme issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/ckanext-dcor_theme.svg
   :target: https://github.com/DCOR-dev/ckanext-dcor_theme/issues
.. |ckanext-dcor_theme pypi|
   image:: https://img.shields.io/pypi/v/ckanext-dcor_theme.svg
   :target: https://pypi.python.org/pypi/ckanext-dcor_theme
.. |ckanext-dcor_theme actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/ckanext-dcor_theme/check.yml
   :target: https://github.com/DCOR-dev/ckanext-dcor_theme/actions/workflows/check.yml
.. |ckanext-dcor_theme cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dcor_theme
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dcor_theme

.. |dcor-remote-tests issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/dcor-remote-tests.svg
   :target: https://github.com/DCOR-dev/dcor-remote-tests/issues
.. |dcor-remote-tests actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/dcor-remote-tests/check.yml
   :target: https://github.com/DCOR-dev/dcor-remote-tests/actions/workflows/check.yml
.. |dcor-remote-tests cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/dcor-remote-tests
   :target: https://codecov.io/gh/DCOR-dev/dcor-remote-tests

.. |dcor_control issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/dcor_control.svg
   :target: https://github.com/DCOR-dev/dcor_control/issues
.. |dcor_control pypi|
   image:: https://img.shields.io/pypi/v/dcor_control.svg
   :target: https://pypi.python.org/pypi/dcor_control
.. |dcor_control actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/dcor_control/check.yml
   :target: https://github.com/DCOR-dev/dcor_control/actions/workflows/check.yml
.. |dcor_control cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/dcor_control
   :target: https://codecov.io/gh/DCOR-dev/dcor_control

.. |dcor_shared issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/dcor_shared.svg
   :target: https://github.com/DCOR-dev/dcor_shared/issues
.. |dcor_shared pypi|
   image:: https://img.shields.io/pypi/v/dcor_shared.svg
   :target: https://pypi.python.org/pypi/dcor_shared
.. |dcor_shared actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/dcor_shared/check.yml
   :target: https://github.com/DCOR-dev/dcor_shared/actions/workflows/check.yml
.. |dcor_shared cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/dcor_shared
   :target: https://codecov.io/gh/DCOR-dev/dcor_shared

.. |DCOR-Aid issu|
   image:: https://img.shields.io/github/issues/DCOR-dev/DCOR-Aid.svg
   :target: https://github.com/DCOR-dev/DCOR-Aid/issues
.. |DCOR-Aid pypi|
   image:: https://img.shields.io/pypi/v/dcoraid.svg
   :target: https://pypi.python.org/pypi/DCOR-Aid
.. |DCOR-Aid actn|
   image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/DCOR-Aid/check.yml
   :target: https://github.com/DCOR-dev/DCOR-Aid/actions/workflows/check.yml
.. |DCOR-Aid cvrg|
   image:: https://img.shields.io/codecov/c/github/DCOR-dev/DCOR-Aid
   :target: https://codecov.io/gh/DCOR-dev/DCOR-Aid

.. |user help issues|
   image:: https://img.shields.io/github/issues/DCOR-dev/DCOR-help.svg
   :target: https://github.com/DCOR-dev/DCOR-help/issues
