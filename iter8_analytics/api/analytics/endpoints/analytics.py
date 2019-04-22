"""
REST resources related to canary analytics.
"""

import iter8_analytics.api.analytics.request_parameters as request_parameters
from iter8_analytics.api.restplus import api
from flask_restplus import Resource

import logging
log = logging.getLogger(__name__)

analytics_namespace = api.namespace(
    'analytics',
    description='Operations to support canary releases and A/B tests')


#################
# REST API
#################

@analytics_namespace.route('/canary/check_and_increment')
class CanaryTest(Resource):

    @api.expect(request_parameters.check_and_increment_parameters,
                validate=True)
    def post(self):
        """Assess the canary version and recommend traffic-control actions."""
        log.info('Started processing request to assess the canary using the '
                 '"check_and_increment" strategy')
        return {'status': 'OK'}
