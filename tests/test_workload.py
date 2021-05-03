"""Test cases for the Workload object."""
import json
import logging
import os
from os.path import abspath
from os.path import dirname
from os.path import join
from typing import Any
from typing import Dict
from typing import List
from unittest.mock import MagicMock
from unittest.mock import patch

import boto3  # type: ignore
import pytest
from moto import mock_ec2  # type: ignore

from tf_restore_helper import Workload


@pytest.fixture
def plan() -> str:
    """Returns a json string."""
    plan_file = join(dirname(abspath(__file__)), "assets/plan.json")
    with open(plan_file) as file:
        plan = file.read()
    return plan


@pytest.fixture
def volumes() -> List[Dict[Any, Any]]:
    """Returns a dict containing aws ebs volumes."""
    volumes_file = join(dirname(abspath(__file__)), "assets/volumes.json")
    with open(volumes_file) as volume_file:
        volumes: List[Dict[Any, Any]] = json.loads(volume_file.read())
    return volumes


@pytest.fixture(scope="function")
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # noqa
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # noqa
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # noqa
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # noqa


@pytest.fixture(scope="function")
def ec2(aws_credentials: Dict[Any, Any]) -> boto3.client:
    """Returns a mocked ec2 boto client."""
    with mock_ec2():
        yield boto3.client("ec2", region_name="eu-west-1")


@pytest.fixture
def workload(plan: str, ec2: boto3.client) -> Workload:
    """Returns a workload object."""
    workload = Workload(plan, ec2)
    return workload


def test_logger_object(workload: Workload) -> None:
    """Tests the logger object is created."""
    assert isinstance(workload.logger, logging.Logger)


@patch.object(Workload, "cloud_volumes")
def test_cloud_volumes(workload: Workload, volumes: List[Dict[Any, Any]]) -> None:
    """Test patched volumes attribute."""
    workload.cloud_volumes = volumes  # type: ignore
    volumes = [
        volume.get("VolumeId", "").startswith("vol-")
        for volume in workload.cloud_volumes
    ]
    assert volumes
    assert all(volumes)


def test_tf_ebs_volumes(workload: Workload) -> None:
    """Test volumes are correctly collected."""
    volumes = [
        volume.get("values", {}).get("id").startswith("vol-")
        for volume in workload.tf_ebs_volumes
    ]
    assert volumes
    assert all(volumes)


def test_flattened_plan(workload: Workload) -> None:
    """Test json plan is flattened correctly."""
    flattened_plan = workload.flattened_plan
    assert {"providers", "resources"}.issubset(set(flattened_plan.keys()))


@patch.object(Workload, "cloud_volumes")
def test_volume_attachment_removal(
    inp: MagicMock, workload: Workload, volumes: List[Dict[Any, Any]]
) -> None:
    """Tests attachment removal."""
    workload.cloud_volumes = volumes  # type: ignore
    print(workload.cloud_volumes)
    assert workload._should_remove_attachment("vol-0000000000000001") is False
    assert workload._should_remove_attachment("vol-0000000000000002") is True


@patch.object(Workload, "cloud_volumes")
def test_terraform_update_data(
    inp: MagicMock, workload: Workload, volumes: List[Dict[Any, Any]]
) -> None:
    """Tests terraform update data."""
    workload.cloud_volumes = volumes  # type: ignore
    assert workload.terraform_update_data[0].new_volume_id == "vol-0000000000000001"
    assert workload.terraform_update_data[0].device_name == "/dev/sdf"
    assert workload.terraform_update_data[0].instance_id == "i-0e00000000000078"
    assert (
        workload.terraform_update_data[0].terraform_attachment_address
        == "aws_volume_attachment.test-instance-volume-1"
    )
    assert (
        workload.terraform_update_data[0].terraform_ebs_volume_address
        == "aws_ebs_volume.test-instance-volume-1"
    )
