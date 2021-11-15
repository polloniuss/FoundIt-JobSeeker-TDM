# -*- codinKeyErrorg: utf-8 -*-

import json
from os import getenv

from flask import Flask, request
from jinja2 import Environment
import structlog

from logger import configure_stdout_logging
from urllib.request import Request, urlopen

import requests
from serpapi import GoogleSearch

def setup_logger():
    logger = structlog.get_logger(__name__)
    try:
        log_level = getenv("LOG_LEVEL", default="INFO")
        configure_stdout_logging(log_level)
        return logger
    except BaseException:
        logger.exception("exception during logger setup")
        raise


logger = setup_logger()
app = Flask(__name__)
environment = Environment()


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending error response to TDM", response=response)
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending query response to TDM", response=response)
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
     """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending multiple query response to TDM", response=response)
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending validator response to TDM", response=response)
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
     """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending dummy query response to TDM", response=response)
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
     }
   }
   """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending successful action response to TDM", response=response)
    return response

def get_data(location, query):
    params = {
        "api_key": "ff1938ebaffa284b0538ad1e53b013782557f8705e2aa5f9c5ad7fb1e5e87ea9",
        "engine": "google_jobs",
        "google_domain": "google.com",
        "q": query,
        "gl": "us",
        "hl": "en",
        "chips": "date_posted:week",
        "Irad": "10",
        "location": location
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    try :            
        jobs = results["jobs_results"]
        data = {}
        try :
            for x in range(3):
                data[x] = [jobs[x]["title"],jobs[x]["company_name"],jobs[x]["location"],jobs[x]["extensions"],jobs[x]["via"]]
                #title = jobs[x]["title"]
                #co_name = jobs[x]["company_name"]
                #loc = jobs[x]["location"]
                #extension = jobs[x]["extensions"]
            str_result0 = [" First job opportunity:",data[0][0],"for",data[0][1],"in",data[0][2],data[0][3],". You can find this job",data[0][4]]
            str_result1 = [". Second job opportunity:",data[1][0],"for",data[1][1],"in",data[1][2],data[1][3],". You can find this job",data[1][4]]
            str_result2 = [". Third job opportunity:",data[2][0],"for",data[2][1],"in",data[2][2],data[2][3],". You can find this job",data[2][4],"."]
            listToStr0 = ' '.join([str(elem) for elem in str_result0])
            listToStr1 = ' '.join([str(elem) for elem in str_result1])
            listToStr2 = ' '.join([str(elem) for elem in str_result2])
            answer = listToStr0 + listToStr1 + listToStr2
            print("!!!!!!!!???????",answer)
            return answer
        
        except IndexError:
            jobs = results["jobs_results"]
            data = {}
            str_result0 = [" First job opportunity:",data[0][0],"for",data[0][1],"in",data[0][2],data[0][3],". You can find this job",data[0][4]]
            answer = ' '.join([str(elem) for elem in str_result0])
            print("!!!!!!!!*******",answer)
            return answer

    except KeyError:
        answer = "There is no result for this query. Try with other parameters."
        print("??????*******",answer)
        return answer


@app.route("/job_seeker", methods=['POST'])
def job_seeker():
    payload = request.get_json()
    field = payload["context"]["facts"]["field_to_search"]["grammar_entry"]
    country = payload["context"]["facts"]["country_to_search"]["grammar_entry"]
    city = payload["context"]["facts"]["city_to_search"]["grammar_entry"]
    contract = payload["context"]["facts"]["contract_to_search"]["grammar_entry"]

    location = city + " " + country

    try:
        option = payload["context"]["facts"]["extra_info_to_search"]["grammar_entry"]
        query = field + " " + contract + " " + option
        data = get_data(location, query)
        return query_response(value=str(data), grammar_entry=None)

    except KeyError:
        query = field + " " + contract
        data = get_data(location, query)
        return query_response(value=str(data), grammar_entry=None)

