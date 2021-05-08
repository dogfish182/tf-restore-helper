Tf Restore Helper
=================

|PyPI| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/tf-restore-helper.svg
   :target: https://pypi.org/project/tf-restore-helper/
   :alt: PyPI
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/tf-restore-helper
   :target: https://pypi.org/project/tf-restore-helper
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/tf-restore-helper
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/tf-restore-helper/latest.svg?label=Read%20the%20Docs
   :target: https://tf-restore-helper.readthedocs.io/
   :alt: Read the documentation at https://tf-restore-helper.readthedocs.io/
.. |Tests| image:: https://github.com/dogfish182/tf-restore-helper/workflows/Tests/badge.svg
   :target: https://github.com/dogfish182/tf-restore-helper/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/dogfish182/tf-restore-helper/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/dogfish182/tf-restore-helper
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black


Features
--------


* Constructs Terraform import commands to assist an operator aligning a terraform state after volume restores have taken place by an external tool, which results in terraform misalignment.

* Tool is currently only compatible with AWS volumes (PRs welcome) and is used at own risk. Operators that do not understand the terraform state file or what the produced commands will do, should not use this tool as a helper and proper state backup and recovery procedures should be well understood before making use of this.


Installation
------------

You can install *Tf Restore Helper* via pip_ from PyPI_:

.. code:: console

   $ pip install tf-restore-helper


Usage
-----

Please see the `Command-line Reference <Usage_>`_ for details.

Examples of usage:

.. code:: console

   > tf-restore-helper --planfile tests/assets/plan.json
    2021-05-03 13:28:43 sbpltc1nplvdl botocore.credentials[79705] INFO Found credentials in environment variables.
    2021-05-03 13:28:46 sbpltc1nplvdl postrestoretfcli[79705]   WARNING THIS INFORMATION SHOULD BE USED ONLY IF YOU KNOW WHAT YOU ARE DOING!
    -----------Terraform volume alignment commands-----------
    terraform state rm "aws_ebs_volume.test-instance-volume-1"
    terraform state rm "aws_volume_attachment.test-instance-volume-1"

Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the `MIT license`_,
*Tf Restore Helper* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------

This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/dogfish182/tf-restore-helper/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://tf-restore-helper.readthedocs.io/en/latest/usage.html
