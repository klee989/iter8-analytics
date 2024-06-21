"""Tests for module iter8_analytics.api.v2"""
# standard python stuff
import copy
from datetime import datetime, timezone, timedelta
import json
import logging
import os

# python libraries
import requests_mock
import pytz
from freezegun import freeze_time

from iter8_analytics import fastapi_app
from iter8_analytics.api.v2.types import \
    ExperimentResource, AggregatedMetricsAnalysis, VersionAssessmentsAnalysis, \
    WinnerAssessmentAnalysis, WeightsAnalysis, VersionWeight
from iter8_analytics.config import env_config
import iter8_analytics.constants as constants
from iter8_analytics.api.v2.examples.examples_canary import \
    er_example, er_example_step1, er_example_step2, er_example_step3, \
    am_response, va_response, wa_response, w_response, mr_example, mocked_mr_example

from iter8_analytics.api.v2.examples.examples_ab import \
    ab_er_example, ab_er_example_step1, ab_er_example_step2, ab_er_example_step3, \
    ab_am_response, ab_va_response, ab_wa_response, ab_w_response, ab_mr_example

from iter8_analytics.api.v2.examples.examples_abn import \
    abn_er_example, abn_er_example_step1, abn_er_example_step2, abn_er_example_step3, \
    abn_am_response, abn_va_response, abn_wa_response, abn_w_response, abn_mr_example

from iter8_analytics.api.v2.metrics import get_aggregated_metrics
from iter8_analytics.api.v2.experiment import get_version_assessments, get_winner_assessment, \
    get_weights, get_analytics_results


logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

logger.info(env_config)


# class TestExperiment:
#     """Test Iter8 v2 experiment"""

def test_input_object():
    ExperimentResource(** er_example)
    ExperimentResource(** er_example_step1)
    ExperimentResource(** er_example_step2)
    ExperimentResource(** er_example_step3)

def test_experiment_response_objects():
    AggregatedMetricsAnalysis(** am_response)
    VersionAssessmentsAnalysis(** va_response)
    WinnerAssessmentAnalysis(** wa_response)
    WeightsAnalysis(** w_response)

def test_aggregated_metrics_endpoint():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        response_json = json.load(open(file_path))
        mock.get(er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=response_json)

        expr = ExperimentResource(** er_example)
        agm = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()
        assert agm.data['request-count'].data['default'].value == \
            response_json['data']['result'][0]['value'][1]

        ercopy = copy.deepcopy(er_example)
        del ercopy["status"]["metrics"]
        expr = ExperimentResource(** ercopy)
        agm = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()

def test_version_assessment_endpoint():
    expr = ExperimentResource(** er_example_step1)
    get_version_assessments(expr.convert_to_float())

def test_winner_assessment_endpoint():
    expr = ExperimentResource(** er_example_step2)
    get_winner_assessment(expr.convert_to_float())

def test_weights_endpoint():
    expr = ExperimentResource(** er_example_step3)
    get_weights(expr.convert_to_float())

def test_analytics_assessment_endpoint():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        expr = ExperimentResource(** er_example)
        get_analytics_results(expr.convert_to_float()).convert_to_quantity()

def test_mock_metrics():
    ercopy = copy.deepcopy(er_example)
    ercopy["status"]["metrics"] = mocked_mr_example
    expr = ExperimentResource(** ercopy)

    agm = get_aggregated_metrics(
        expr.convert_to_float())
    logger.info(agm)
    assert agm.data['request-count'].data['default'].value > 100.0
    assert agm.data['request-count'].data['canary'].value > 100.0
    assert agm.data['mean-latency'].data['default'].value > 15.0
    assert agm.data['mean-latency'].data['canary'].value > 9.0

def test_mock_metrics_with_negative_elapsed():
    ercopy = copy.deepcopy(er_example)
    ercopy["status"]["metrics"] = mocked_mr_example
    expr = ExperimentResource(** ercopy)
    expr.status.startTime = datetime.now(timezone.utc) + timedelta(hours=10)

    agm = get_aggregated_metrics(
        expr.convert_to_float())
    logger.info(agm)
    assert agm.data['request-count'].data['default'].value > 0
    assert agm.data['request-count'].data['canary'].value > 0
    assert agm.data['mean-latency'].data['default'].value > 0
    assert agm.data['mean-latency'].data['canary'].value > 0

def test_am_without_candidates():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))
        example = copy.deepcopy(er_example)
        del example['spec']['versionInfo']['candidates']
        expr = ExperimentResource(** example)
        get_aggregated_metrics(expr.convert_to_float()).convert_to_quantity()

def test_analytics_assessment_conformance():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(er_example)
        del example['spec']['versionInfo']['candidates']
        example['spec']['strategy']['testingPattern'] = 'Conformance'
        expr = ExperimentResource(** example)
        get_analytics_results(expr.convert_to_float()).convert_to_quantity()

def test_version_assessment_conformance():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(er_example)
        del example['spec']['versionInfo']['candidates']
        example['spec']['strategy']['testingPattern'] = 'Conformance'
        expr = ExperimentResource(** example)
        resp = get_analytics_results(
            expr.convert_to_float()).convert_to_quantity()
        assert resp.version_assessments.data == {'default': [True]}

def test_va_without_am():
    expr = ExperimentResource(** er_example)
    try:
        get_version_assessments(expr.convert_to_float())
    except AttributeError:
        pass

def test_wa_without_va():
    expr = ExperimentResource(** er_example)
    try:
        get_winner_assessment(expr.convert_to_float())
    except AttributeError:
        pass

def test_w_without_wa():
    expr = ExperimentResource(** er_example)
    try:
        get_weights(expr.convert_to_float())
    except AttributeError:
        pass

@freeze_time("2012-01-14 03:21:34", tz_offset=-4)
def test_no_prometheus_response():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_no_response.json')
        mock.get(er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        expr = ExperimentResource(** er_example)
        resp = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()
        expected_response = {
            "request-count": {
                "max": None,
                "min": None,
                "data": {
                    "default": {
                        "max": None,
                        "min": None,
                        "sample_size": None,
                        "value": None,
                        "history": [(datetime(2012, 1, 13, 23, 21, 34, tzinfo=pytz.utc), None)],
                    },
                    "canary": {
                        "max": None,
                        "min": None,
                        "sample_size": None,
                        "value": None,
                        "history": [(datetime(2012, 1, 13, 23, 21, 34, tzinfo=pytz.utc), None)],
                    }
                }
            },
            "mean-latency": {
                "max": None,
                "min": None,
                "data": {
                    "default": {
                        "max": None,
                        "min": None,
                        "sample_size": None,
                        "value": None,
                        "history": [(datetime(2012, 1, 13, 23, 21, 34, tzinfo=pytz.utc), None)],
                    },
                    "canary": {
                        "max": None,
                        "min": None,
                        "sample_size": None,
                        "value": None,
                        "history": [(datetime(2012, 1, 13, 23, 21, 34, tzinfo=pytz.utc), None)],
                    }
                }
            }
        }
        assert resp.data == expected_response

def test_va_with_no_metric_value():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_no_response.json')
        mock.get(er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        expr = ExperimentResource(** er_example)
        resp = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()

        example = copy.deepcopy(er_example_step1)
        example['status']['analysis']["aggregatedMetrics"] = resp
        expr = ExperimentResource(** example)
        resp2 = get_version_assessments(expr.convert_to_float())

        assert resp2.data == {'default': [False], 'canary': [False]}

def test_va_without_mean_latency_metric():
    example = copy.deepcopy(er_example_step1)
    example['status']['analysis']['aggregatedMetrics']["data"].pop(
        'mean-latency', None)
    expr = ExperimentResource(** example)
    resp = get_version_assessments(expr.convert_to_float())
    assert resp.message == \
        "Error: ; Warning: Aggregated metric object for mean-latency metric is unavailable.; Info: "

def test_canary_passing_criteria():
    example = copy.deepcopy(er_example_step1)
    example['spec']['criteria']['objectives'][0]['upperLimit'] = 500
    expr = ExperimentResource(** example)
    resp = get_version_assessments(expr.convert_to_float())
    assert resp.data == {'default': [True], 'canary': [True]}

def test_canary_failing_upperlimit_criteria():
    expr = ExperimentResource(** er_example_step1)
    resp = get_version_assessments(expr.convert_to_float())
    assert resp.data == {'default': [True], 'canary': [False]}

def test_canary_failing_lowerlimit_criteria():
    example = copy.deepcopy(er_example_step1)
    example['spec']['criteria']['objectives'][0].pop('upperLimit')
    example['spec']['criteria']['objectives'][0]['lowerLimit'] = 500
    expr = ExperimentResource(** example)
    resp = get_version_assessments(expr.convert_to_float())
    assert resp.data == {'default': [False], 'canary': [False]}

def test_canary_is_winner():
    example = copy.deepcopy(er_example_step2)

    example['status']['analysis']['versionAssessments'] = {
        "data": {
            "default": [
                True
            ],
            "canary": [
                True
            ]
        },
        "message": "All ok"
    }
    expr = ExperimentResource(** example)
    resp = get_winner_assessment(expr.convert_to_float())
    assert resp.data.winnerFound == wa_response['data']['winnerFound']
    assert resp.data.winner == wa_response['data']['winner']

def test_analytics_assessment_conformance_winner():
    example = copy.deepcopy(er_example_step2)

    example['status']['analysis']['versionAssessments'] = {
        "data": {
            "default": [
                True
            ]
        },
        "message": "All ok"
    }
    del example['spec']['versionInfo']['candidates']
    example['spec']['strategy']['testingPattern'] = 'Conformance'
    expr = ExperimentResource(** example)
    resp = get_winner_assessment(expr.convert_to_float())
    assert resp.data.winnerFound is True
    assert resp.data.winner == 'default'

def test_default_is_winner():
    example = copy.deepcopy(er_example_step2)

    example['status']['analysis']['versionAssessments'] = {
        "data": {
            "default": [
                True
            ],
            "canary": [
                False
            ]
        },
        "message": "All ok"
    }
    expr = ExperimentResource(** example)
    resp = get_winner_assessment(expr.convert_to_float())

    assert resp.data.winnerFound == wa_response['data']['winnerFound']
    assert resp.data.winner == 'default'

def test_no_winner():
    example = copy.deepcopy(er_example_step2)

    example['status']['analysis']['versionAssessments'] = {
        "data": {
            "default": [
                False
            ],
            "canary": [
                False
            ]
        },
        "message": "All ok"
    }
    expr = ExperimentResource(** example)
    resp = get_winner_assessment(expr.convert_to_float())

    assert resp.data.winnerFound is False

def test_weights_with_winner():
    expr = ExperimentResource(** er_example_step3)
    resp = get_weights(expr.convert_to_float())

    expected_resp = [
        VersionWeight(name="default", value=5),
        VersionWeight(name="canary", value=95)
    ]
    assert resp.data == expected_resp

def test_weights_with_no_winner():
    example = copy.deepcopy(er_example_step3)
    example['status']['analysis']['winnerAssessment']['data'] = {
        "winnerFound": False
    }
    expr = ExperimentResource(** example)
    resp = get_weights(expr.convert_to_float())
    assert resp.data == w_response['data']

def test_inc_old_weights_and_best_versions_and_canary_winner():
    example = copy.deepcopy(er_example_step3)
    example['status']['currentWeightDistribution'] = [{
        "name": "default",
        "value": 70

    }, {
        "name": "canary",
        "value": 30

    }]
    expected_resp = [{
        "name": "default",
        "value": 5

    }, {
        "name": "canary",
        "value": 95

    }]
    expr = ExperimentResource(** example)
    resp = get_weights(expr.convert_to_float())
    assert resp.data == expected_resp

def test_inc_old_weights_and_no_best_versions():
    example = copy.deepcopy(er_example_step3)
    example['status']['currentWeightDistribution'] = [{
        "name": "default",
        "value": 50

    }, {
        "name": "canary",
        "value": 50

    }]
    example["status"]["analysis"]["winnerAssessment"]["data"] = {
        "winnerFound": False
    }
    expected_resp = [{
        "name": "default",
        "value": 95

    }, {
        "name": "canary",
        "value": 5

    }]
    expr = ExperimentResource(** example)
    resp = get_weights(expr.convert_to_float())
    assert resp.data == expected_resp

def test_set_weights_config():
    example = copy.deepcopy(er_example_step3)
    example['status']['currentWeightDistribution'] = [{
        "name": "default",
        "value": 50

    }, {
        "name": "canary",
        "value": 50

    }]

    example['spec']['strategy']['weights'] = {
        "maxCandidateWeight": 53,
        "maxCandidateWeightIncrement": 2,
        "algorithm": 'Progressive'
    }

    expected_resp = [{
        "name": "default",
        "value": 48

    }, {
        "name": "canary",
        "value": 52

    }]
    expr = ExperimentResource(** example)
    resp = get_weights(expr.convert_to_float())
    assert resp.data == expected_resp


def test_using_previous_metric_status():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                 'prometheus_sample_no_response.json')
        mock.get(er_example["status"]["metrics"][0]["metricObj"]
                 ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(er_example_step1)

        example['status']['metrics'] = mr_example
        expr = ExperimentResource(** example)
        resp = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()

        expected_response = copy.deepcopy(am_response)
        assert resp.data['mean-latency'].data['default'].value == \
            expected_response['data']['mean-latency']['data']['default']['value']


########## A/B TESTS #############
def test_ab_input_object():
    ExperimentResource(** ab_er_example)
    ExperimentResource(** ab_er_example_step1)
    ExperimentResource(** ab_er_example_step2)
    ExperimentResource(** ab_er_example_step3)

def test_experiment_ab_response_objects():
    AggregatedMetricsAnalysis(** ab_am_response)
    VersionAssessmentsAnalysis(** ab_va_response)
    WinnerAssessmentAnalysis(** ab_wa_response)
    WeightsAnalysis(** ab_w_response)

def test_ab_aggregated_metrics_endpoint():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        response_json = json.load(open(file_path))
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=response_json)

        expr = ExperimentResource(** ab_er_example)
        agm = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()
        assert agm.data['request-count'].data['default'].value == \
            response_json['data']['result'][0]['value'][1]

def test_ab_version_assessment_endpoint():
    expr = ExperimentResource(** ab_er_example_step1)
    get_version_assessments(expr.convert_to_float())

def test_ab_winner_assessment_endpoint():
    expr = ExperimentResource(** ab_er_example_step2)
    get_winner_assessment(expr.convert_to_float())

def test_ab_weights_endpoint():
    expr = ExperimentResource(** ab_er_example_step3)
    get_weights(expr.convert_to_float())

def test_ab_analytics_assessment_endpoint():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        expr = ExperimentResource(** ab_er_example)
        get_analytics_results(expr.convert_to_float()).convert_to_quantity()

def test_ab_reward_only_analytics_assessment_endpoint():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        ab_expr = copy.deepcopy(ab_er_example)
        del ab_expr["spec"]["criteria"]["objectives"]
        expr = ExperimentResource(** ab_expr)
        get_analytics_results(expr.convert_to_float()).convert_to_quantity()

def test_ab_am_without_candidates():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))
        example = copy.deepcopy(ab_er_example)
        del example['spec']['versionInfo']['candidates']
        expr = ExperimentResource(** example)
        get_aggregated_metrics(expr.convert_to_float()).convert_to_quantity()

def test_ab_analytics_assessment_conformance():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(ab_er_example)
        del example['spec']['versionInfo']['candidates']
        example['spec']['strategy']['testingPattern'] = 'Conformance'
        expr = ExperimentResource(** example)
        get_analytics_results(expr.convert_to_float()).convert_to_quantity()

def test_conformance_without_objectives():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(ab_er_example)
        del example['spec']['versionInfo']['candidates']
        del example['spec']['criteria']['objectives']
        del example['spec']['criteria']['rewards']
        example['spec']['strategy']['testingPattern'] = 'Conformance'
        expr = ExperimentResource(** example)
        get_analytics_results(expr.convert_to_float()).convert_to_quantity()

def test_ab_version_assessment_conformance():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(ab_er_example)
        del example['spec']['versionInfo']['candidates']
        example['spec']['strategy']['testingPattern'] = 'Conformance'
        expr = ExperimentResource(** example)
        resp = get_analytics_results(
            expr.convert_to_float()).convert_to_quantity()
        assert resp.version_assessments.data == {'default': [True]}

def test_ab_va_without_am():
    expr = ExperimentResource(** ab_er_example)
    try:
        get_version_assessments(expr.convert_to_float())
    except AttributeError:
        pass

def test_ab_wa_without_va():
    expr = ExperimentResource(** ab_er_example)
    try:
        get_winner_assessment(expr.convert_to_float())
    except AttributeError:
        pass

def test_ab_w_without_wa():
    expr = ExperimentResource(** ab_er_example)
    try:
        get_weights(expr.convert_to_float())
    except AttributeError:
        pass

def test_ab_without_reward():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))
        example = copy.deepcopy(ab_er_example)
        del example['spec']['criteria']['rewards']
        expr = ExperimentResource(** example)
        resp = get_analytics_results(
            expr.convert_to_float()).convert_to_quantity()
        assert "No reward metric in experiment" in resp.winner_assessment.message
        assert resp.winner_assessment.data.winnerFound is False

def test_ab_without_reward_metric_config():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))
        example = copy.deepcopy(ab_er_example)
        del example["status"]["metrics"][2]
        expr = ExperimentResource(** example)
        resp = get_analytics_results(
            expr.convert_to_float()).convert_to_quantity()

        assert "reward metric values are not available" in \
            resp.winner_assessment.message
        assert resp.winner_assessment.data.winnerFound is False

def test_ab_without_reward_for_feasible_version():
    example = copy.deepcopy(ab_er_example_step2)

    del example['status']['analysis']['aggregatedMetrics']['data']['business-revenue']['data']['canary']
    expr = ExperimentResource(** example)
    resp = get_winner_assessment(expr.convert_to_float())
    assert "reward value for feasible version canary is not available" in \
        resp.message


def test_ab_using_previous_metric_status():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                 'prometheus_sample_no_response.json')
        mock.get(ab_er_example["status"]["metrics"][0]["metricObj"]
                 ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(ab_er_example_step1)

        example['status']['metrics'] = ab_mr_example[:2]
        expr = ExperimentResource(** example)
        resp = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()

        expected_response = copy.deepcopy(ab_am_response)
        assert resp.data['mean-latency'].data['default'].value == \
            expected_response['data']['mean-latency']['data']['default']['value']

########## A/B/N TESTS #############
def test_abn_input_object():
    ExperimentResource(** abn_er_example)
    ExperimentResource(** abn_er_example_step1)
    ExperimentResource(** abn_er_example_step2)
    ExperimentResource(** abn_er_example_step3)

def test_experiment_abn_response_objects():
    AggregatedMetricsAnalysis(** abn_am_response)
    VersionAssessmentsAnalysis(** abn_va_response)
    WinnerAssessmentAnalysis(** abn_wa_response)
    WeightsAnalysis(** abn_w_response)

def test_abn_aggregated_metrics_endpoint():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        response_json = json.load(open(file_path))
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=response_json)

        expr = ExperimentResource(** abn_er_example)
        agm = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()
        assert agm.data['request-count'].data['default'].value == \
            response_json['data']['result'][0]['value'][1]

def test_abn_version_assessment_endpoint():
    expr = ExperimentResource(** abn_er_example_step1)
    get_version_assessments(expr.convert_to_float())

def test_abn_winner_assessment_endpoint():
    expr = ExperimentResource(** abn_er_example_step2)
    get_winner_assessment(expr.convert_to_float())

def test_abn_weights_endpoint():
    expr = ExperimentResource(** abn_er_example_step3)
    get_weights(expr.convert_to_float())

def test_abn_analytics_assessment_endpoint():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        expr = ExperimentResource(** abn_er_example)
        get_analytics_results(expr.convert_to_float()).convert_to_quantity()

def test_abn_am_without_candidates():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))
        example = copy.deepcopy(abn_er_example)
        del example['spec']['versionInfo']['candidates']
        expr = ExperimentResource(** example)
        get_aggregated_metrics(expr.convert_to_float()).convert_to_quantity()

def test_abn_analytics_assessment_conformance():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(abn_er_example)
        del example['spec']['versionInfo']['candidates']
        example['spec']['strategy']['testingPattern'] = 'Conformance'
        expr = ExperimentResource(** example)
        get_analytics_results(expr.convert_to_float()).convert_to_quantity()

def test_abn_version_assessment_conformance():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(abn_er_example)
        del example['spec']['versionInfo']['candidates']
        example['spec']['strategy']['testingPattern'] = 'Conformance'
        expr = ExperimentResource(** example)
        resp = get_analytics_results(
            expr.convert_to_float()).convert_to_quantity()
        assert resp.version_assessments.data == {'default': [True]}

def test_abn_va_without_am():
    expr = ExperimentResource(** abn_er_example)
    try:
        get_version_assessments(expr.convert_to_float())
    except AttributeError:
        pass

def test_abn_wa_without_va():
    expr = ExperimentResource(** abn_er_example)
    try:
        get_winner_assessment(expr.convert_to_float())
    except AttributeError:
        pass

def test_abn_w_without_wa():
    expr = ExperimentResource(** abn_er_example)
    try:
        get_weights(expr.convert_to_float())
    except AttributeError:
        pass

def test_abn_without_reward():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))
        example = copy.deepcopy(abn_er_example)
        del example['spec']['criteria']['rewards']
        expr = ExperimentResource(** example)
        resp = get_analytics_results(
            expr.convert_to_float()).convert_to_quantity()
        assert "No reward metric in experiment" in \
            resp.winner_assessment.message
        assert resp.winner_assessment.data.winnerFound is False

def test_abn_without_reward_metric_config():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                    'prometheus_sample_response.json')
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                ["spec"]["urlTemplate"], json=json.load(open(file_path)))
        example = copy.deepcopy(abn_er_example)
        del example["status"]["metrics"][2]
        expr = ExperimentResource(** example)
        resp = get_analytics_results(
            expr.convert_to_float()).convert_to_quantity()

        assert "reward metric values are not available" in \
                resp.winner_assessment.message
        assert resp.winner_assessment.data.winnerFound is False

def test_abn_general():
    example = copy.deepcopy(abn_er_example_step2)

    expr = ExperimentResource(** example)
    resp = get_winner_assessment(expr.convert_to_float())
    assert resp.data.winnerFound is True
    assert resp.data.winner == 'canary1'

def test_abn_without_reward_for_feasible_version():
    example = copy.deepcopy(abn_er_example_step2)

    del example['status']['analysis']['aggregatedMetrics']['data']['business-revenue']['data']['canary1']
    expr = ExperimentResource(** example)
    resp = get_winner_assessment(expr.convert_to_float())
    assert "reward value for feasible version canary1 is not available" in \
        resp.message
    assert resp.data.winnerFound is True
    assert resp.data.winner == 'canary2'

def test_abn_with_better_reward_but_not_feasible():
    example = copy.deepcopy(abn_er_example_step2)

    example['status']['analysis']['versionAssessments']['data']['canary1'] = [False]
    expr = ExperimentResource(** example)
    resp = get_winner_assessment(expr.convert_to_float())
    assert resp.data.winnerFound is True
    assert resp.data.winner == 'canary2'


def test_abn_using_previous_metric_status():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                 'prometheus_sample_no_response.json')
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                 ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(abn_er_example_step1)

        example['status']['metrics'] = abn_mr_example[:2]
        expr = ExperimentResource(** example)
        resp = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()

        expected_response = copy.deepcopy(abn_am_response)
        assert resp.data['mean-latency'].data['default'].value == \
            expected_response['data']['mean-latency']['data']['default']['value']


def test_abn_using_previous_metric_status_none():
    with requests_mock.mock(real_http=True) as mock:
        file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                 'prometheus_sample_no_response.json')
        mock.get(abn_er_example["status"]["metrics"][0]["metricObj"]
                 ["spec"]["urlTemplate"], json=json.load(open(file_path)))

        example = copy.deepcopy(abn_er_example)

        example['status']['metrics'] = abn_mr_example[:2]
        expr = ExperimentResource(** example)
        resp = get_aggregated_metrics(
            expr.convert_to_float()).convert_to_quantity()
        assert resp.data['mean-latency'].data['default'].value is None
