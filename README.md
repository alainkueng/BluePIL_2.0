# BluePIL Bluetooth Passive Identification and Localization

## Installation Guidelines

BluePIL 2.0 requires Python v3.8 to be installed. A virtual environment
capable of running both the host and the sink code can then be installed
by running `pip install -r requirements.txt`.

Dependencies for the BluePIL node code to run on an Raspberry Pi can be installed
by running the script `node_setup/install.sh` on the device.

The BluePIL node mini-server can be started by running `python raspberry_server.py`.

The BluePIL sink application can be started by running `python run_sink.py`.

The application can be configured using the file `bp.json` or after the sink application has started.

For each node (`node1-4`), the following options must be set:
* `True Point`: x, y coordinates of the to be sensed device
* `N-Value`: the n coefficient value
* `Ubertooth 1-4`: x, y coordinates of the Uberteeth within the scenario

After the configuration the streaming pipeline can be started by typing \texttt{START\textunderscore NODE}. 
Demo.mp4 in the Root Directory shows a short demonstration of the setup.

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