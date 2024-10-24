from mars_lib.models.isa_json import Investigation
from mars_lib.authentication import get_webin_auth_token
from mars_lib.biosamples_external_references import (
    get_header,
    biosamples_endpoints,
    BiosamplesRecord,
    validate_json_against_schema,
    input_json_schema_filepath,
)
from mars_lib.isa_json import reduce_isa_json_for_target_repo
from mars_lib.target_repo import TargetRepository
from mars_lib.credential import CredentialManager
import requests
from typing import Any


def submission(
    username_credentials, isa_json_file, target_repositories, investigation_is_root
):
    cm = CredentialManager("mars-cli")
    pwd = cm.get_password_keyring(username_credentials)

    if TargetRepository.ENA in target_repositories:
        target_repositories.pop(TargetRepository.BIOSAMPLES)

    if TargetRepository.ENA in target_repositories:
        submit_to_ena()
    elif TargetRepository.BIOSAMPLES in target_repositories:
        # Submit to Biosamples
        biosamples_credentials = {"username": username_credentials, "password": pwd}
        submit_to_biosamples(
            isa_json_file, biosamples_credentials, biosamples_endpoints["prod"]
        )
    elif TargetRepository.METABOLIGHTS in target_repositories:
        # Submit to MetaboLights
        pass
    elif TargetRepository.EVA in target_repositories:
        # Submit to EVA
        pass
    else:
        raise ValueError("No target repository selected.")


def submit_to_biosamples(
    investiagation: Investigation,
    biosamples_credentials: dict[str, str],
    url: str,
) -> requests.Response:

    params = {"webinjwt": get_webin_auth_token(biosamples_credentials)}
    headers = {"accept": "*/*", "Content-Type": "application/json"}
    return requests.post(url, headers=headers, params=params, json=investiagation)


def create_external_references(
    biosamples_credentials: dict[str, str],
    biosamples_externalReferences: dict[str, Any],
    production: bool,
) -> None:
    """
    Main function to be executed when script is run.

    Args:
    biosamples_credentials: Dictionary with the credentials of the submitter of the existing Biosamples records.
    biosamples_externalReferences: Dictionary containing the mapping between the
    production: Boolean indicating the environment of BioSamples to use.
    """
    if production:
        biosamples_endpoint = biosamples_endpoints["prod"]
    else:
        biosamples_endpoint = biosamples_endpoints["dev"]

    validate_json_against_schema(
        json_doc=biosamples_externalReferences, json_schema=input_json_schema_filepath
    )
    token = get_webin_auth_token(biosamples_credentials)
    if not token:
        raise ValueError("The token could not be generated.")
    header = get_header(token)

    for biosample_r in biosamples_externalReferences["biosampleExternalReferences"]:
        bs_accession = biosample_r["biosampleAccession"]
        BSrecord = BiosamplesRecord(bs_accession)
        BSrecord.fetch_bs_json(biosamples_endpoint)
        # To test it without the fetching, you can download it manually and then use:
        #   BSrecord.load_bs_json(bs_json_file="downloaded-json.json")
        new_ext_refs_list = biosample_r["externalReferences"]
        BSrecord.extend_externalReferences(new_ext_refs_list)
        BSrecord.update_remote_record(header)


def submit_to_ena():
    pass
