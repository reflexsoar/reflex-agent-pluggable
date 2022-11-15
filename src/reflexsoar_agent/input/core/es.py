import json
import ssl

from elasticsearch import (ApiError, AuthenticationException, BadRequestError,
                           Elasticsearch)
from opensearchpy import OpenSearch
from retry import retry

from reflexsoar_agent.core.logging import logger
from reflexsoar_agent.input import BaseInput
from reflexsoar_agent.input.base import InputTypes


class ElasticInput(BaseInput):

    def __init__(self, alias: str, input_type: str = InputTypes.POLL,
                 config: dict = None, credentials: tuple = None):
        super().__init__(alias, input_type, config)

        self.config = config
        self.status = 'waiting'
        self.credentials = credentials
        self.conn = self.build_es_connection()
        self.plugin_type = input_type

    def build_es_connection(self):
        '''
        Creates an Elasticsearch connection object that can
        be used to query Elasticsearch
        '''

        # Create an empty configuration object
        es_config = {
        }

        # If we are defining a ca_file use ssl_contexts with the ca_file
        # else disable ca_certs and verify_certs and don't use ssl_context
        if self.config['cafile'] != "":

            context = ssl.create_default_context(cafile=self.config['cafile'])
            CONTEXT_VERIFY_MODES = {
                "none": ssl.CERT_NONE,
                "optional": ssl.CERT_OPTIONAL,
                "required": ssl.CERT_REQUIRED
            }

            context.verify_mode = CONTEXT_VERIFY_MODES[self.config['cert_verification']]
            context.check_hostname = self.config['check_hostname']
            es_config['ssl_context'] = context
        else:
            # es_config['ca_certs'] = False
            es_config['verify_certs'] = False
            es_config['ssl_show_warn'] = False  # Disable SSL warnings
            # es_config['ssl_assert_hostname'] = self.config['check_hostname']

        # Set the API Authentication method
        if self.config['auth_method'] == 'api_key':
            es_config['api_key'] = self.credentials
        else:
            es_config['http_auth'] = self.credentials

        if 'no_scroll' not in self.config:
            self.config['no_scroll'] = False

        # Swap distros depending on the inputs configuration
        if 'distro' in self.config:
            if self.config['distro'] == 'opensearch':
                return OpenSearch(self.config['hosts'], **es_config)
            else:
                # http_auth deprecated in future versions of elasticsearch-py
                if 'http_auth' in es_config:
                    es_config['basic_auth'] = es_config.pop('http_auth')

                return Elasticsearch(self.config['hosts'], **es_config)
        else:
            # http_auth deprecated in future versions of elasticsearch-py
            if 'http_auth' in es_config:
                es_config['basic_auth'] = es_config.pop('http_auth')

            return Elasticsearch(self.config['hosts'], **es_config)

    def _build_query_body(self, search_period: str, lucene_filter: str, size: int) -> dict:
        """Builds the query body for the Elasticsearch query.

        Args:
            search_period (str): The time period to search for events.
            lucene_filter (str): The Lucene filter to apply to the query.
            size (int): The number of events to return.
        """
        query_body = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": f"now-{search_period}"
                            }
                        }
                    }
                ]
            }
        }

        if lucene_filter:
            filter_query = {"query_string": {"query": lucene_filter}}
            query_body['bool']['must'].append(filter_query)

        print(json.dumps(query_body, indent=2))

        return query_body

    @retry(ApiError, tries=3, delay=2, backoff=2)
    def poll(self) -> list:  # noqa: C901
        """Polls an Elasticsearch instance for data."""

        events = []
        error = False

        search_period = self.config.get('search_period', '5m')  # Default to 5 minutes
        lucene_filter = self.config.get('lucene_filter', None)
        search_size = self.config.get('search_size', 1000)
        index = self.config.get('index', None)

        if index in [None, ""]:
            logger.error(f"Index not specified for {self.alias}")
            return []

        query_body = self._build_query_body(search_period, lucene_filter, search_size)

        search_params = {
            'index': index,
            'query': query_body,
            'size': search_size,
            'scroll': '2m'
        }

        if 'distro' in self.config and self.config['distro'] == 'opensearch':
            search_params['body'] = {"query": search_params.pop('query')}

        try:
            res = self.conn.search(**search_params)
            scroll_id = res['_scroll_id']
            if 'total' in res['hits']:
                logger.info(
                    f"Found {res['hits']['total']['value']} total events in {index}")
                scroll_size = search_size
                events += res['hits']['hits']
            else:
                scroll_size = 0

            while scroll_size > 0 and self.config['no_scroll'] is False:

                # If the input is configured to only return a maximum number of
                # hits per poll break out of the loop when this number is
                # reached or surpassed
                if 'max_hits' in self.config and self.config['max_hits']:
                    if len(events) >= self.config['max_hits']:
                        logger.warning(
                            f"Max hits {self.config['max_hits']} reached for {self.alias}")
                        break

                logger.info(f"Scrolling {scroll_size} events in {index}")
                res = self.conn.scroll(scroll_id=scroll_id, scroll='2m')
                if 'total' in res['hits'] and res['hits']['total']['value'] > 0:
                    events += res['hits']['hits']

                scroll_size = len(res['hits']['hits'])

        except AuthenticationException as e:
            logger.error(f"Authentication failed for {self.alias}. {e}")
            error = True
        except BadRequestError as e:
            logger.error(f"Bad request for {self.alias}: {e}")
            error = True
        except ApiError as e:
            logger.error(f"API error for {self.alias}: {e}")
            error = True

        if error:
            return []

        return events

    def run(self):
        raise NotImplementedError
