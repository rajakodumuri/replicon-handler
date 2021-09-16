import json
import time
import logging

# Connections to the Replicon API are made possible with requests library.
import requests

# Asynchronous functionality is built using asyncio and aiohttp.
import asyncio
import aiohttp

# Threading is built using concurrent futures.
from concurrent.futures import ThreadPoolExecutor, as_completed

# Variables for use in the code build.
# Replicon Tenant Access Details.
REPLICON_COMPANY_KEY = None
REPLICON_TENANT_USERNAME = None
REPLICON_TENANT_PASSWORD = None
# Logging and Connection Headers.
LOG_FILE = None
CONNECTION_HEADERS = None

# Logger Configuration
logging.basicConfig(
    filemode='w',
    filename=LOG_FILE,
    level=logging.DEBUG,
    datefmt='%m/%d/%Y %H:%M:%S',
    format='%(levelname)s %(asctime)s %(message)s'
)


def simple_handler(connector, headers, payload, auth):
    """Handling all connections."""

    log_payload = json.dumps(payload)

    if auth is not None:
        auth = (f'{REPLICON_COMPANY_KEY}\{REPLICON_TENANT_USERNAME}',
                REPLICON_TENANT_PASSWORD)

    url_caller = requests.post(
        url=connector, headers=headers, data=json.dumps(payload), auth=auth)

    correlation_id = url_caller.headers['x-execution-correlation-id']
    result = url_caller.json()
    error_in_result = result.get('error')

    logging.debug(f"Correlation ID: {correlation_id}")

    if error_in_result:
        logging.error(
            f"Payload: {log_payload} Response: {error_in_result}")
        return error_in_result

    logging.info(f"Payload: {log_payload} Response: {result}")
    return result


def connection_handler(connector, headers, payload, auth):
    """Handling connection exceptions."""

    log_payload = json.dumps(payload)

    try:
        result = simple_handler(connector, headers, payload, auth)
    except Exception as exception:
        exception_type = exception.__class__.__name__
        logging.error(
            f'Payload: {log_payload} Exception: {exception_type} {exception}')

        # Attempting the failed operation again.
        print(f'Exception: {exception_type}. Retrying in a moment.')
        time.sleep(20)
        result = simple_handler(connector, headers, payload, auth)

    return result


def threaded_connection_handler(connector, headers, payloads, auth, workers):
    """Handling connections asynchronously for faster execution."""

    counter, results = 0, []

    with ThreadPoolExecutor(max_workers=workers) as thread_pool_executor:
        executor = {thread_pool_executor.submit(
            connection_handler, connector, headers, payload, auth): payload for payload in payloads}

        for result in as_completed(executor):
            counter += 1
            print(f'Current Processed Entry: {counter}')
            results.append(result.result())

    return results


def get_replicon_application_urls(company_key):
    """Gathering Replicon Tenant Swimlane Details."""

    # Tenant details URL.
    get_tenant_details = 'https://global.replicon.com/DiscoveryService1.svc/GetTenantEndpointDetails'

    swimlane_finder_headers = {'content-type': 'application/json'}

    # Payload Body Creation.
    payload = {}
    tenant = {}
    tenant['companyKey'] = company_key
    payload['tenant'] = tenant

    # Getting swimlane information from the Company Key
    tenant_details = connection_handler(
        get_tenant_details, swimlane_finder_headers, payload, None)

    application_root_urls = tenant_details['d']['applicationRootUrls']

    tenant_slug = tenant_details['d']['tenant']['slug']

    gen3_swimlane = tenant_details['d']['applicationRootUrl']

    gen3_source_swimlane = gen3_swimlane.split('//')
    gen3_source_swimlane = '//src-'.join(gen3_source_swimlane)

    polaris_swimlane = application_root_urls[0]['rootUrl']

    replicon_urls = (tenant_slug, gen3_swimlane,
                     gen3_source_swimlane, polaris_swimlane)

    return replicon_urls


# Setting up Application Details
(
    TENANT_SLUG,
    GEN3_SWIMLANE,
    GEN3_SOURCE_SWIMLANE,
    POLARIS_SWIMLANE
) = get_replicon_application_urls(REPLICON_COMPANY_KEY)


def replicon_web_service(webService, serviceComponent):
    return f"{GEN3_SWIMLANE}services/{webService}/{serviceComponent}"


def replicon_source_web_service(webService, serviceComponent):
    return f"{GEN3_SOURCE_SWIMLANE}services/{webService}/{serviceComponent}"


def replicon_polaris_graphql():
    return f"{POLARIS_SWIMLANE}graphql"
