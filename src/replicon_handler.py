import os
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


class RepliconHandler:
    """Handling all Replicon related functions with this."""

    essentials = ['company_key', 'username', 'password',
                  'authentication_token', 'method', 'headers', 'log_path']

    def __init__(self, **kwargs):
        """Instantiating the Replicon operation handler class."""

        # Validating existence of necessary instantiation variables.
        for essential in self.essentials:
            if essential not in kwargs.keys():
                message = f'Essential Key: {essential} is missing.'
                notices = f'Check initialization of RepliconHandler.'
                raise KeyError(f'{message} {notices}')

        # Setting up tenant details.
        if kwargs['company_key']:
            self.company_key = kwargs['company_key']
        else:
            raise ValueError(f'Company Key is required.')

        # Setting up authentication details.
        if kwargs['username'] and kwargs['password']:
            self.username = kwargs['username']
            self.password = kwargs['password']
            self.authentication_token = None
        elif kwargs['authentication_token']:
            self.username, self.password = None, None
            self.authentication_token = kwargs['authentication_token']
        else:
            raise ValueError(f'Credentials or Token is mandatory.')

        # Evaluating HTTP method used for operations.
        if kwargs['method'] and kwargs['method'] in ['post', 'get']:
            self.method = kwargs['method']
        else:
            raise ValueError(f'Method must be "post" or "get".')

        # Setting up basic headers, meeting Replicon requirements.
        if kwargs['headers']:
            self.headers = kwargs['headers']

            for header in ['Content-Type', 'X-Replicon-Application']:
                if header not in self.headers.keys():
                    raise KeyError(f'{header} is not included in the headers.')

            application = self.headers['X-Replicon-Application']
            version = 'Replicon-Handler-v1.1.7'
            application_version = f'{application}; v={version}'
            self.headers['X-Replicon-Application'] = application_version
        else:
            raise ValueError(f'Headers are mandatory.')

        # Setting up a path to place operational activity logs in.
        if kwargs['log_path']:
            log_path = rf"{kwargs['log_path']}\Replicon-Activity-Logs"
            if not os.path.exists(log_path):
                os.mkdir(log_path)

            self.log_path = log_path
            self.log_time = time.strftime('%Y%m%d%H%M%S', time.localtime())
            self.log_file_name = f'{self.company_key}_log_{self.log_time}.log'
            self.log_file = rf'{self.log_path}\{self.log_file_name}'
        else:
            log_path = rf"{os.getcwd()}\Replicon-Activity-Logs"
            if not os.path.exists(log_path):
                os.mkdir(log_path)

            self.log_path = log_path
            self.log_time = time.strftime('%Y%m%d%H%M%S', time.localtime())
            self.log_file_name = f'{self.company_key}_log_{self.log_time}.log'
            self.log_file = rf'{self.log_path}\{self.log_file_name}'

        # Allowing flexibility to set up logging levels manually.
        log_level = 'logger_level'
        manual_level = log_level in kwargs.keys() and kwargs[log_level]
        self.log_level = kwargs[log_level] if manual_level else logging.DEBUG

        # Logger Configuration
        logging.basicConfig(
            filemode='w', filename=self.log_file,
            level=self.log_level, datefmt='%m/%d/%Y %H:%M:%S',
            format='%(levelname)s %(asctime)s %(message)s'
        )

        # Setting up Replicon Global Domain.
        self.global_domain = 'https://global.replicon.com'

        # Setting up Replicon Tenant Details.
        (
            self.tenant_slug, self.swimlane,
            self.source_swimlane, self.polaris
        ) = self.get_application_details()

    @staticmethod
    def post_request(connector, headers, payload, auth):
        """Handling Post Requests related to Replicon API."""

        log_payload, url_caller = json.dumps(payload), requests.post(
            url=connector, headers=headers, data=json.dumps(payload), auth=auth)

        status_code = url_caller.status_code

        if status_code == 429:
            return status_code, 'API Calls Limit Reached.'

        correlation_id = url_caller.headers['x-execution-correlation-id']
        logging.debug(f'Correlation ID: {correlation_id}')

        result = url_caller.json()
        error_in_result = result.get('error')
        log_message = f'Payload: {log_payload} Response: {result}'

        if error_in_result:
            logging.error(log_message)
            return status_code, error_in_result

        logging.info(log_message)
        return status_code, result

    @staticmethod
    def get_request(connector, headers, payload, auth):
        """Handling Get Requests related to Replicon API."""

        log_payload, url_caller = json.dumps(payload), requests.get(
            url=connector, headers=headers, params=payload, auth=auth)

        status_code = url_caller.status_code

        if status_code == 429:
            return status_code, 'API Calls Limit Reached.'

        correlation_id = url_caller.headers['x-execution-correlation-id']
        logging.debug(f'Correlation ID: {correlation_id}')

        result = url_caller.json()
        error_in_result = result.get('error')
        log_message = f'Payload: {log_payload} Response: {result}'

        if error_in_result:
            logging.error(log_message)
            return status_code, error_in_result

        logging.info(log_message)
        return status_code, error_in_result

    @staticmethod
    def till_next_hour(now):
        """Evaluating time delta between now and the next hour."""
        return (60 * 60) - (now.minute * 60 + now.second)

    def connection_handler(self, connector, payload):
        """Handling connections, exceptions and API Limitations."""

        log_payload = json.dumps(payload)
        method, headers = self.method, self.headers
        authentication = None if self.authentication_token else (
            rf'{self.company_key}\{self.username}', self.password
        )

        try:
            if method == 'post':
                status_code, result = self.post_request(
                    connector, headers, payload, authentication)
                if status_code == 429:
                    # API Limits: Initiating the operation in the next hour.
                    logging.error(f'Limited. Status Code: {status_code}.')
                    time.sleep(self.till_next_hour(datetime.datetime.now()))
                    return self.connection_handler(connector, payload)
            else:
                status_code, result = self.get_request(
                    connector, headers, payload, authentication)
                if status_code == 429:
                    # API Limits: Initiating the operation in the next hour.
                    logging.error(f'Limited. Status Code: {status_code}.')
                    time.sleep(self.till_next_hour(datetime.datetime.now()))
                    return self.connection_handler(connector, payload)

        except Exception as exception:
            exception_type = exception.__class__
            exception_name = exception_type.__name__
            retry_worthy = [requests.ConnectionError, requests.HTTPError]
            exception_message = f'Exception: {exception_name} {exception}'
            logging.error(f'Payload: {log_payload} {exception_message}')

            if exception_type in retry_worthy:
                # Retry the failed operation after a short gap.
                print(f'Exception: {exception_name}. Retrying in a moment.')
                time.sleep(20)
                return self.connection_handler(connector, payload)
            else:
                # Raise the exception to be handled by the invoker.
                raise exception_type(f'{exception}')

        return result

    def threaded_handler(self, connector, payloads, workers):
        """Handling connections asynchronously for faster execution."""

        counter, results = 0, list()

        with ThreadPoolExecutor(max_workers=workers) as threaded_executor:
            executor = {threaded_executor.submit(
                self.connection_handler, connector, payload
            ): payload for payload in payloads}

            for result in as_completed(executor):
                counter += 1
                print(f'Current Processed Entry: {counter}')
                results.append(result.result())

        return results

    def get_application_details(self):
        """Gathering Replicon Tenant Swimlane Details."""

        # Tenant details service URL.
        get_tenant_details = self.global_services(
            'DiscoveryService1.svc', 'GetTenantEndpointDetails')

        swimlane_finder_headers = {
            'content-type': 'application/json',
            'X-Replicon-Application': self.headers['X-Replicon-Application']
        }

        # Payload Body Creation.
        payload, tenant = dict(), dict()
        tenant['companyKey'], payload['tenant'] = self.company_key, tenant

        # Getting swimlane information from the Company Key
        status_code, tenant_details = self.post_request(
            get_tenant_details, swimlane_finder_headers, payload, None)

        root_urls = tenant_details['d']['applicationRootUrls']
        slug = tenant_details['d']['tenant']['slug']
        swimlane = tenant_details['d']['applicationRootUrl']
        source_swimlane = '//src-'.join(swimlane.split('//'))
        polaris = root_urls[0]['rootUrl']

        application_details = (slug, swimlane, source_swimlane, polaris)

        return application_details

    def global_services(self, service, component, additional=None):
        """Generating Replicon Global Service URLs."""
        if additional:
            return f'{self.global_domain}/{additional}/{service}/{component}'

        return f'{self.global_domain}/{service}/{component}'

    def web_service(self, service, component, source=False):
        """Generating Replicon Web Service URLs."""
        if source:
            return f'{self.source_swimlane}services/{service}/{component}'

        return f'{self.swimlane}services/{service}/{component}'

    def graphql(self):
        """Generating Replicon GraphQL URL."""
        return f'{self.polaris}graphql'

    def webhooks(self):
        """Generating Replicon Webhook API GraphQL URL."""
        return f'{self.swimlane}webhook-api/graphql'

    def user_audit_logs(self):
        """Generating Replicon User Audit Logs URL."""
        return f'{self.swimlane}adminapi/audit-logs'

    def analytics_extracts(self, extract_id=None):
        """Generating URLs to Get/Create Replicon Analytics Extract(s)."""
        if extract_id:
            return f'{self.swimlane}analytics/extracts/{extract_id}'

        return f'{self.swimlane}analytics/extracts'

    def analytics_tables(self, table_id=None):
        """Generating URL to Get Replicon Analytics Table(s)."""
        if table_id:
            return f'{self.swimlane}analytics/tables/{table_id}'

        return f'{self.swimlane}analytics/tables'
