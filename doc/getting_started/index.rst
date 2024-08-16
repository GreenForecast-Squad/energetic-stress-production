Getting Started
===============

Project description
-------------------
See the :doc:`project description <project_description>` for a detailed description of the project.


Data sources
------------

See the :doc:`data sources <data_sources>` for a detailed description of the data sources available
and the corresponding way to access them.

Installation
------------
You can install the package from the source code by cloning the repository and
using
`Hatch <https://hatch.pypa.io/latest/>`_ to install the package.

.. code-block:: bash

    git clone https://github.com/GreenForecast-Squad/energetic-stress-production
    pipx install hatch
    cd energy-forecast
    hatch shell

This will open a new shell with the hatch environment and the package installed


Running the dashboard
---------------------

To launche the vizual interface, run the dashboard with the following command:

.. code-block:: bash

    hatch run serve:prod

With will launch a Streamlit app on the port ``8502`` of ``localhost``.
You can access the app by opening a browser and going to the following URL: http://localhost:8502/energy_forecast .


Detailed use cases
==================

To see move detailed use cases, you can check the tutorials in the :doc:`../user_guide/index` !

.. toctree::
   :maxdepth: 2
   :hidden:

   project_description
   data_sources
