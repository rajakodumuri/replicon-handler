import json
import time
import logging
import datetime

# Connections to the Replicon API are made possible with requests library.
import requests

# Asynchronous functionality is built using asyncio and aiohttp.
import asyncio
import aiohttp

# Threading is built using concurrent futures.
from concurrent.futures import ThreadPoolExecutor, as_completed


class RepliconHandler():
    """Handling all Replicon related functions with this."""

    def __init__(self, **kwargs):
        """Instantiating the Replicon operation handler class."""

        # Setting up tenant details.
        self.company_key = kwargs['company_key']

        # Setting up authentication details.
        self.authentication_token = kwargs['authentication_token']
        self.username = kwargs['username']
        self.password = kwargs['password']

        # Setting up requirements for successful operations.
        self.method = kwargs['method']
        self.headers = kwargs['headers']
        self.log_file = kwargs['log_file']

        # Setting up Application Details
        (
            self.tenant_swimlane,
            self.gen3_swimlane,
            self.gen3_source_swimlane,
            self.polaris_swimlane
        ) = self.get_application_details()

        # Logger Configuration
        logging.basicConfig(
            filemode='w',
            filename=self.log_file,
            level=logging.DEBUG,
            datefmt='%m/%d/%Y %H:%M:%S',
            format='%(levelname)s %(asctime)s %(message)s'
        )

    def post_request(self, connector, headers, payload, auth):
        """Handling Post Requests related to Replicon API."""

        log_payload = json.dumps(payload)

        url_caller = requests.post(
            url=connector, headers=headers, data=json.dumps(payload), auth=auth)

        status_code = url_caller.status_code
        correlation_id = url_caller.headers['x-execution-correlation-id']
        logging.debug(f'Correlation ID: {correlation_id}')

        result = url_caller.json()
        error_in_result = result.get('error')

        if error_in_result:
            logging.error(
                f'Payload: {log_payload} Response: {error_in_result}')
            return status_code, error_in_result

        logging.info(f'Payload: {log_payload} Response: {result}')
        return status_code, result

    def get_request(self, connector, headers, payload, auth):
        """Handling Get Requests related to Replicon API."""

        log_payload = json.dumps(payload)

        url_caller = requests.get(
            url=connector, headers=headers, params=payload, auth=auth)

        status_code = url_caller.status_code
        correlation_id = url_caller.headers['x-execution-correlation-id']
        logging.debug(f'Correlation ID: {correlation_id}')

        result = url_caller.json()
        error_in_result = result.get('error')

        if error_in_result:
            logging.error(
                f'Payload: {log_payload} Response: {error_in_result}')
            return status_code, error_in_result

        logging.info(f'Payload: {log_payload} Response: {result}')
        return status_code, error_in_result

    def till_next_hour(now):
        """Evaluating time delta between now and the next hour."""
        return (60 * 60) - (now.minute * 60 + now.second)

    def connection_handler(self, connector, payload):
        """
            Handling connections based on:
            - Methods
            - API Limitations
            - Connection Exceptions
        """

        method = self.method
        headers = self.headers
        log_payload = json.dumps(payload)
        authentication = (f'{self.company_key}\{self.username}',
                          self.password) if not self.authentication_token else self.authentication_token

        try:
            if method == 'post':
                status_code, result = self.post_request(
                    connector, headers, payload, authentication)
                if status_code == 429:
                    # API Limits: Initiating the operation in the next hour.
                    logging.error(f'Limited. Status Code: {status_code}.')
                    self.till_next_hour(datetime.datetime.now())
                    return self.connection_handler(connector, payload)
            else:
                status_code, result = self.get_request(
                    connector, headers, payload, authentication)
                if status_code == 429:
                    # API Limits: Initiating the operation in the next hour.
                    logging.error(f'Limited. Status Code: {status_code}.')
                    self.till_next_hour(datetime.datetime.now())
                    return self.connection_handler(connector, payload)

        except Exception as exception:
            exception_type = exception.__class__.__name__
            logging.error(
                f'Payload: {log_payload} Exception: {exception_type} {exception}')

            # Attempting the failed operation again.
            print(f'Exception: {exception_type}. Retrying in a moment.')
            time.sleep(20)
            return self.connection_handler(connector, payload)

        return result

    def threaded_handler(self, connector, payloads, workers):
        """Handling connections asynchronously for faster execution."""

        counter, results = 0, []

        with ThreadPoolExecutor(max_workers=workers) as threaded_executor:
            executor = {threaded_executor.submit(
                self.connection_handler, connector, payload): payload for payload in payloads}

            for result in as_completed(executor):
                counter += 1
                print(f'Current Processed Entry: {counter}')
                results.append(result.result())

        return results

    def get_application_details(self):
        """Gathering Replicon Tenant Swimlane Details."""

        # Tenant details URL.
        get_tenant_details = 'https://global.replicon.com/DiscoveryService1.svc/GetTenantEndpointDetails'

        swimlane_finder_headers = {'content-type': 'application/json'}

        # Payload Body Creation.
        payload = {}
        tenant = {}
        tenant['companyKey'] = self.company_key
        payload['tenant'] = tenant

        # Getting swimlane information from the Company Key
        tenant_details = self.post_request(
            get_tenant_details, swimlane_finder_headers, payload, None)

        application_root_urls = tenant_details['d']['applicationRootUrls']

        tenant_slug = tenant_details['d']['tenant']['slug']

        gen3_swimlane = tenant_details['d']['applicationRootUrl']

        gen3_source_swimlane = gen3_swimlane.split('//')
        gen3_source_swimlane = '//src-'.join(gen3_source_swimlane)

        polaris_swimlane = application_root_urls[0]['rootUrl']

        application_details = (tenant_slug, gen3_swimlane,
                               gen3_source_swimlane, polaris_swimlane)

        return application_details

    def web_service(self, webService, serviceComponent):
        """Generating Replicon Web Service URL."""
        return f'{self.gen3_swimlane}services/{webService}/{serviceComponent}'

    def source_web_service(self, webService, serviceComponent):
        """Generating Replicon Source Web Service URL."""
        return f'{self.gen3_source_swimlane}services/{webService}/{serviceComponent}'

    def graphql(self):
        """Generating Replicon GraphQL URL."""
        return f'{self.polaris_swimlane}graphql'

    def audit_log(self):
        """Generating Replicon User Audit Log URL."""
        return f'{self.gen3_swimlane}adminapi/audit-logs'

    def analytics_extracts(self):
        """Generating URL to Get/Create Replicon Analytics Extract(s)."""
        return f'{self.gen3_swimlane}analytics/extracts'

    def analytics_extract(self, extract_id):
        """Generating URL to Get Replicon Analytics Extract Details"""
        return f'{self.gen3_swimlane}analytics/extracts/{extract_id}'

    def analytics_tables(self):
        """Generating URL to Get All Replicon Analytics Tables."""
        return f'{self.gen3_swimlane}analytics/tables'

    def analytics_table(self, table_id):
        """Generating URL to Get Details of a Replicon Analytics Table."""
        return f'{self.gen3_swimlane}analytics/tables/{table_id}'
