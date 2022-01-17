#!/usr/bin/env python
"""Command-line interface."""
import json
import logging.config
import sys
from typing import Optional

import click
import coloredlogs  # type: ignore

from tf_restore_helper import get_aws_client
from tf_restore_helper import Workload

# This is the main prefix used for logging
LOGGER_BASENAME = """tf-restore-helper"""
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())
logging.getLogger("botocore").setLevel(logging.INFO)


def setup_logging(level: str, config_file: Optional[str] = None) -> None:
    """Sets up the logging.

    Needs the args to get the log level supplied
    Args:
        level: At which level do we log
        config_file: Configuration to use
    """
    # This will configure the logging, if the user has set a config file.
    # If there's no config file, logging will default to stdout.
    if config_file:
        # Get the config for the logger. Of course this needs exception
        # catching in case the file is not there and everything. Proper IO
        # handling is not shown here.
        try:
            with open(config_file) as conf_file:
                configuration = json.loads(conf_file.read())
                # Configure the logger
                logging.config.dictConfig(configuration)
        except ValueError:
            print(f'File "{config_file}" is not valid json, cannot continue.')
            raise SystemExit(1) from ValueError
    else:
        coloredlogs.install(level=level.upper())


@click.command()
@click.option(
    "--planfile", "-p", required=True, help="A terraform plan file in json format."
)
@click.option("--debug", is_flag=True, help="Set debug logging on.")
@click.option("--logconfig", help="The path to a custom logging config file")
@click.version_option()
def main(planfile: str, debug: bool, logconfig: Optional[str] = None) -> None:
    """Constructs terraform commands to run to re-align terraform plans with the state of the cloud."""
    logging_level = "DEBUG" if debug else "INFO"
    setup_logging(level=logging_level, config_file=logconfig)
    try:
        with open(planfile, "r") as file:
            plan = file.read()
    except FileNotFoundError:
        LOGGER.error("Please provide a valid path for a terraform plan file.")
        sys.exit(1)
    try:
        json.loads(plan)
    except json.decoder.JSONDecodeError:
        LOGGER.error("The terraform plan file supplied is not valid json.")
        sys.exit(1)
    ec2 = get_aws_client("ec2")
    if not ec2:
        LOGGER.error("Ensure you have valid aws credentials before using this tool.")
        sys.exit(1)
    account = Workload(plan, ec2)
    if account.terraform_update_data:
        LOGGER.warning(
            "THIS INFORMATION SHOULD BE USED ONLY IF YOU KNOW WHAT YOU ARE DOING!"
        )
        for data in account.terraform_update_data:
            print("-----------Terraform volume alignment commands-----------")
            print(f'terraform state rm "{data.terraform_ebs_volume_address}"')
            print(f'terraform state rm "{data.terraform_attachment_address}"')
            if data.new_volume_id:
                print(
                    f'terraform import "{data.terraform_ebs_volume_address}" "{data.new_volume_id}"'
                )
                print(
                    f'terraform import "{data.terraform_attachment_address}" '
                    f'"{data.device_name}:{data.new_volume_id}:{data.instance_id}"'
                )
        return
    LOGGER.info("No alignment actions required for this account with this plan")


if __name__ == "__main__":
    main(prog_name="tf-restore-helper")  # pragma: no cover
