"""Main code."""
import itertools
import logging
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import boto3  # type: ignore
import botocore  # type: ignore
from flatplan import PlanFlattener  # type: ignore

# This is the main prefix used for logging
LOGGER_BASENAME = """postrestoretfcli"""
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


class LoggerMixin:  # pylint: disable=too-few-public-methods
    """Logger."""

    @property
    def logger(self) -> logging.Logger:
        """Exposes the logger to be used by objects using the Mixin.

        Returns:
            logger (logger): The properly named logger.

        """
        return logging.getLogger(f"{LOGGER_BASENAME}.{self.__class__.__name__}")


@dataclass
class TerraformImportData:
    """Class for keeping track disk details required for terraform import."""

    new_volume_id: str
    device_name: str
    instance_id: str
    terraform_attachment_address: str
    terraform_ebs_volume_address: str


class Workload(LoggerMixin):
    """Models an aws account configured with terraform."""

    def __init__(self, plan: str, client: boto3.client) -> None:
        """Properties for the workload."""
        self.client = client
        self.plan = plan
        self._flattened_plan: Dict[Any, Any] = {}
        self._cloud_volumes: List[Dict[Any, Any]] = []
        self._tf_ebs_attachments: List[Any] = []
        self._tf_ebs_volumes: List[Any] = []
        self._terraform_data: List[Any] = []

    @property
    def cloud_volumes(self) -> List[Dict[Any, Any]]:
        """Return all cloud volumes for account."""
        if not self._cloud_volumes:
            paginator = self.client.get_paginator("describe_volumes")
            pages = paginator.paginate()
            self._cloud_volumes = list(
                itertools.chain.from_iterable([page.get("Volumes") for page in pages])
            )
        return self._cloud_volumes

    @property
    def flattened_plan(self) -> Dict[Any, Any]:
        """Return the flattened terraform plan."""
        if not self._flattened_plan:
            self._flattened_plan = PlanFlattener(self.plan).flatten()
        return self._flattened_plan

    @property
    def tf_ebs_attachments(self) -> List[Dict[Any, Any]]:
        """Return all ebs attachments recorded in the terraform plan."""
        if not self._tf_ebs_attachments:
            resources = self.flattened_plan.get("resources")
            if resources:
                self._tf_ebs_attachments = [
                    resource
                    for resource in resources
                    if resource.get("type") == "aws_volume_attachment"
                ]
        return self._tf_ebs_attachments

    @property
    def tf_ebs_volumes(self) -> List[Any]:
        """Return all ebs volumes recorded in the terraform plan."""
        if not self._tf_ebs_volumes:
            self._tf_ebs_volumes = [
                resource
                for resource in self.flattened_plan.get("resources")  # type: ignore
                if resource.get("type") == "aws_ebs_volume"
            ]
        return self._tf_ebs_volumes

    @property
    def tf_ebs_volumes_for_removal(self) -> List[Any]:
        """Return all the terraform ebs volumes that should be removed from the state."""
        volumes_to_remove = [
            volume
            for volume in self.tf_ebs_volumes
            if self._should_remove_volume(volume.get("values", {}).get("id"))
        ]
        return volumes_to_remove

    @property
    def tf_ebs_attachments_for_removal(self) -> List[Any]:
        """Return all the ebs attachments that should be removed from the terraform state."""
        attachments_to_remove = [
            attachment
            for attachment in self.tf_ebs_attachments
            if self._should_remove_attachment(
                attachment.get("values", {}).get("volume_id")
            )
        ]
        return attachments_to_remove

    def _get_all_volumes(self) -> List[Any]:
        paginator = self.client.get_paginator("describe_volumes")
        pages = paginator.paginate()
        all_volumes = list(
            itertools.chain.from_iterable([page.get("Volumes") for page in pages])
        )
        return all_volumes

    def _should_remove_volume(self, volume_id: str) -> bool:
        """If the volume is found we should not remove it."""
        for volume in self.cloud_volumes:
            if volume.get("VolumeId") == volume_id:
                return False
        return True

    def _should_remove_attachment(self, volume_id: str) -> bool:
        """If the volume is found AND attached we should not remove it."""
        for volume in self.cloud_volumes:
            if volume.get("VolumeId") == volume_id and volume.get("Attachments"):
                return False
        return True

    def _get_new_volume_id_for_attachment(
        self, device_name: str, instance_id: str
    ) -> Any:
        """Return the new volume id from the cloud volumes."""
        for volume in self.cloud_volumes:
            attachments = volume.get("Attachments")
            if attachments:
                for attachment in attachments:
                    if (
                        attachment.get("Device") == device_name
                        and attachment.get("InstanceId") == instance_id
                    ):
                        return attachment.get("VolumeId")
        return ""

    @property
    def terraform_update_data(self) -> List[Any]:
        """Returns: List of TerraformImport Data objects for constructing terraform commands."""
        terraform_data = []
        for attachment in self.tf_ebs_attachments_for_removal:
            old_volume_id = attachment.get("values").get("volume_id")
            device_name = attachment.get("values").get("device_name")
            instance_id = attachment.get("values").get("instance_id")
            new_volume_id = self._get_new_volume_id_for_attachment(
                device_name, instance_id
            )
            terraform_attachment_address = attachment.get("address")
            terraform_ebs_volume_address = next(
                (
                    volume.get("address")
                    for volume in self.tf_ebs_volumes_for_removal
                    if volume.get("values").get("id") == old_volume_id
                ),
                "",
            )
            terraform_data.append(
                TerraformImportData(
                    new_volume_id,
                    device_name,
                    instance_id,
                    terraform_attachment_address,
                    terraform_ebs_volume_address,
                )
            )
        return terraform_data


def get_aws_client(
    client_type: str, session: boto3.session = None
) -> Union[boto3.client, bool]:
    """Gets a valid boto client."""
    if not session:
        session = boto3.Session()
    sts = session.client("sts")
    try:
        sts.get_caller_identity()
        return session.client(client_type)
    except botocore.exceptions.NoCredentialsError:
        return False
    except botocore.exceptions.ClientError:
        return False
