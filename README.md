# OpenNMS RRDs Sorter

This Python script connects to the Meridian/Horizon REST API to gather a list of nodes and will attempt to move RRD files after switching `org.opennms.rrd.storeByForeignSource` from `false` to `true`.

> [!WARNING]
> This script has not extensively been tested.
> Use at your own risk.

Tested on Python 3.8 and 3.11.

## Setup and Usage

* Install Python dependencies
  * `pip3 install --upgrade -r requirements.txt`
* Run the script
  * `python3 sort_rrd.py`
  * The script will prompt for your RRD path, hostname, and credentials.

If running the script as root, I would suggest running `${OPENNMS_HOME}/bin/fix-permissions` after running this script.

Any errors will be logged to `sort_rrd.log`.
