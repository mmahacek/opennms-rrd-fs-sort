# sort-rrd.py

"Script to sort OpenNMS RRD directories from nodeId to foreignSource/foreignId"

import getpass
import logging
import os
import shutil
from dataclasses import dataclass
from typing import Dict

import pyonms
from pyonms.dao.nodes import NodeComponents
from tqdm import tqdm

log_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [main] (Thread-%(thread)s-%(funcName)s) %(message)s"
)
logger = logging.getLogger("sort_rrd")
logger.setLevel(logging.DEBUG)
bh = logging.FileHandler("./sort_rrd.log")
bh.setFormatter(log_formatter)
bh.setLevel(logging.DEBUG)
logger.addHandler(bh)

remaining_ignore = ["fs"]

@dataclass
class FS_FID:
    fs: str
    fid: str


def main():
    results: Dict[str, int] = {"moved": 0, "missing": 0, "extra": 0}

    rrd_path = input("RRD directory path (do not include trailing slash): ")

    if not rrd_path:
        logger.error("Exiting, RRD path not provided")
        raise ValueError("RRD path not provided")
    else:
        if not os.path.isdir(rrd_path):
            logger.error("Exiting, RRD path does not exist")
            raise FileNotFoundError("RRD path does not exist")

    hostname = input("Enter hostname (defaults to 'http://localhost:8980/opennms'): ")
    username = input("Enter username (defaults to 'admin'): ")
    password = getpass.getpass("Enter password (required): ")
    apply_changes = input("Do you want to move files (If not, dry run will only log proposed changes) [Y/Yes]:")

    if apply_changes.lower in ['y', 'yes']:
        apply_changes = True
    else:
        apply_changes = False
        logger.info("Dry run - no files will be moved")

    if not hostname:
        hostname = "http://localhost:8980/opennms"
    if not username:
        username = "admin"
    if not password:
        logger.error("Exiting, Password not provided")
        raise ValueError("Password not provided")

    server = pyonms.PyONMS(
        hostname=hostname,
        username=username,
        password=password,
    )
    logger.info(f"Connecting to {hostname}")

    logger.info("Gathering nodes")
    nodes = server.nodes.get_nodes(components=[NodeComponents.NONE])

    node_mapping: Dict[int, FS_FID] = {}

    logger.info("Associating node ID with FS:FID")
    for node in tqdm(nodes, unit="node", desc="Parsing node IDs"):
        if node.foreignSource:
            node_mapping[node.id] = FS_FID(fs=node.foreignSource, fid=node.foreignId)

    logger.info("Moving RRD directories")
    for node_id, fs in tqdm(node_mapping.items(), unit="node", desc="Moving RRDs"):
        try:
            if apply_changes:
                shutil.move(f"{rrd_path}/{node_id}", f"{rrd_path}/fs/{fs.fs}/{fs.fid}")
            else:
                remaining_ignore.append("node_id")
            logger.info(
                f"moved: {rrd_path}/{node_id} to {rrd_path}/fs/{fs.fs}/{fs.fid}"
            )
            results["moved"] += 1
        except FileNotFoundError:
            logger.warning(f"missing: {rrd_path}/{node_id} does not exist")
            results["missing"] += 1

    logger.info("Looking for orphaned nodeId metrics")
    remaining = os.listdir(rrd_path)
    for directory in tqdm(
        remaining, unit="directories", desc="Checking for extra directories"
    ):
        if directory in remaining_ignore:
            continue
        logger.warning(
            f"extra: {rrd_path}/{directory} exists but there is no node {directory} currently in inventory."
        )
        results["extra"] += 1

    logger.info("Completed")
    logger.info(f"{results}")
    print(results)


if __name__ == "__main__":
    main()
