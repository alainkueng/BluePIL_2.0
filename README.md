# BluePIL Bluetooth Passive Identification and Localization

## Installation Guidelines

BluePIL requires Python v3.8 to be installed. A virtual environment
capable of running both the host and the sink code can then be installed
by running `pip install -r requirements.txt`.

Dependencies for the BluePIL node code to run on an Asus Tinkerboard running
Armbian can be installed by running the script `node_setup/install.sh` on
the device.

The BluePIL node application can be started by running `python run_node.py`.

The BluePIL sink application can be started by running `python run_sink.py`.

In order for the communication between node and sink to work properly, the node
application has to be started on each node before starting the sink application.

The application can be configured using the file `bp.json`. The following options
are available for the mode:

* `RAW`: lets the nodes collect raw data without running the positioning pipeline and store it on the sink
* `RAW_LOCAL`: lets the nodes collect raw data without running the positioning pipeline and store it locally
* `POSITIONING`: runs the full positioning pipeline and stores the results on the sink

For each node (`node1-4`), the following options must be set:
* `ip`: the ip of the node
* `loc`: the loocation of the node as a tuple of x and y coordinates


## Installation on Asus Tinkerboard Running Armbian

The script `install.sh` (bluepil/node_setup) can be used to install all necessary dependencies, including
Python v3.8, set up a virtual environment, add the necessary USB rules, etc. to run
the BluePIL node code on an Asus Tinkerboard running Armbian

## Possible Ubertooth DFU
*  ATTRS{idVendor}=="ffff", ATTRS{idProduct}=="0004", MODE="0666", GROUP="@UBERTOOTH_GROUP@"
*  Ubertooth Zero
ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="6000", MODE="0666", GROUP="@UBERTOOTH_GROUP@"
*  Ubertooth Zero DFU
ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="6001", MODE="0666", GROUP="@UBERTOOTH_GROUP@"
*  Ubertooth One
ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="6002", MODE="0666", GROUP="@UBERTOOTH_GROUP@"
*  Ubertooth One DFU
ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="6003", MODE="0666", GROUP="@UBERTOOTH_GROUP@"