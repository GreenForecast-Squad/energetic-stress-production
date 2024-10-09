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

Running only tempo predictions
---------------------

if you want to calculate tempo predictions only, run the following command:

.. code-block:: bash

    hatch run tempo_prediction

If you're having an error, similar to 

.. code-block:: bash
    ValueError: unrecognized engine cfgrib must be one of your download engines: ['netcdf4', 'h5netcdf', 'scipy', 'store', 'zarr']

You're having a commun error with cfgrib, you can try to solve it with:

.. code-block:: bash
    sudo apt-get install libeccodes-dev

Also, don't forget to create an account on https://data.rte-france.eu/ to access RTE APIs. You will need to add two APIs to your application :
- "Consumption" https://data.rte-france.eu/catalog/-/api/consumption/Consumption/v1.2
- "Tempo Like Supply Contract" https://data.rte-france.eu/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1  


Detailed use cases
==================

To see move detailed use cases, you can check the tutorials in the :doc:`../user_guide/index` !

.. toctree::
   :maxdepth: 2
   :hidden:

   project_description
   data_sources
