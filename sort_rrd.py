# sort-rrd.py

import getpass
import logging
import os
import shutil
from dataclasses import dataclass
from typing import Dict

import pyonms
from pyonms.dao.nodes import NodeComponents
from tqdm import tqdm

batch_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [main] (Thread-%(thread)s-%(funcName)s) %(message)s"
)
batch_logger = logging.getLogger("sort_rrd")
batch_logger.setLevel(logging.DEBUG)
bh = logging.FileHandler("./sort_rrd.log")
bh.setFormatter(batch_formatter)
bh.setLevel(logging.DEBUG)

batch_logger.addHandler(bh)


@dataclass
class FS_FID:
    fs: str
    fid: str


def main():

    rrd_path = input("RRD directory path (do not include trailing slash): ")

    if not rrd_path:
        batch_logger.error("Exiting, RRD path not provided")
        raise ValueError("RRD path not provided")
    else:
        if not os.path.isdir(rrd_path):
            batch_logger.error("Exiting, RRD path does not exist")
            raise FileNotFoundError("RRD path does not exist")

    hostname = input("Enter hostname (defaults to 'http://localhost:8980/opennms'): ")
    username = input("Enter username (defaults to 'admin'): ")
    password = getpass.getpass("Enter password (required): ")

    if not hostname:
        hostname = "http://localhost:8980/opennms"
    if not username:
        username = "admin"
    if not password:
        batch_logger.error("Exiting, Password not provided")
        raise ValueError("Password not provided")

    server = pyonms.PyONMS(
        hostname=hostname,
        username=username,
        password=password,
    )
    batch_logger.info(f"Connecting to {hostname}")

    batch_logger.info("Gathering nodes")
    nodes = server.nodes.get_nodes(components=[NodeComponents.NONE])

    node_mapping: Dict[int, FS_FID] = {}

    batch_logger.info("Associating node ID with FS:FID")
    for node in tqdm(nodes, unit="node", desc="Parsing node IDs"):
        if node.foreignSource:
            node_mapping[node.id] = FS_FID(fs=node.foreignSource, fid=node.foreignId)

    batch_logger.info("Moving RRD directories")
    for node_id, fs in tqdm(node_mapping.items(), unit="node", desc="Moving RRDs"):
        try:
            shutil.move(f"{rrd_path}/{node_id}", f"{rrd_path}/fs/{fs.fs}/{fs.fid}")
            batch_logger.info(
                f"{rrd_path}/{node_id} moved to {rrd_path}/fs/{fs.fs}/{fs.fid}"
            )
        except FileNotFoundError:
            batch_logger.warning(f"{rrd_path}/{node_id} does not exist")

    batch_logger.info("Completed")


if __name__ == "__main__":
    main()
