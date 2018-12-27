"""Generae weaveworks/grafanalib dashboard file"""
# -*- coding: utf-8 -*-

# from argparse import ArgumentParser
import json
from grafanalib.core import *
from grafanalib.timescale import *

def getYAxes(panelConfig):
    return single_y_axis(
        format=panelConfig["http"]["yAxes"]
    )

def getTargetExpr(customer_id, api_endpoint, httpMethod, graphType):

    if graphType == "==LATENCY==":
        return " SELECT \
            $__timeGroupAlias(hm.t,$__interval), \
            avg(hm.duration) AS \"" + httpMethod + " " + api_endpoint + "\" \
            FROM http_measurements as hm \
            inner join runtimes as rt \
            on rt.id = hm.runtime_id \
            WHERE \
            $__timeFilter(hm.t) AND \
            hm.api_endpoint ~ '" + api_endpoint + "' AND \
            rt.customer_id ~ '" + customer_id + "' AND \
            hm.method = '" + httpMethod + "' \
            GROUP BY 1 \
            ORDER BY 1;"
    elif graphType == "==ERROR==":
        return " SELECT \
            $__timeGroupAlias(hm.t,$__interval), \
            avg(hm.duration) AS \"" + httpMethod + " " + api_endpoint + "\" \
            FROM http_measurements as hm \
            inner join runtimes as rt \
            on rt.id = hm.runtime_id \
            WHERE \
            $__timeFilter(hm.t) AND \
            hm.api_endpoint ~ '" + api_endpoint + "' AND \
            rt.customer_id ~ '" + customer_id + "' AND \
            hm.method = '" + httpMethod + "' \
            GROUP BY 1 \
            ORDER BY 1;" 
    else:
        return ""

def getTargets(customer_id, panelConfig, api_endpoint, graphType):

    targets = []

    httpMethods = panelConfig["http"]["methods"]
    for httpMethod_id in range(len(httpMethods)):
        target = Target(
            rawQuery = True,
            rawSql = getTargetExpr(customer_id, api_endpoint, httpMethods[httpMethod_id], graphType),
            refId = chr(65 + httpMethod_id),
            legendFormat="1xx",
        )
        targets.append(target)

    return targets

# getGraphs will return latency and error graphs
def getGraphs(dataSource, customer_id, panelConfig, api_endpoint, graph_id):

    # latency graph    
    latencyGraph = Graph(
        title = "Avg latency on " + api_endpoint + " endpoint",
        targets = getTargets(customer_id, panelConfig, api_endpoint, "==LATENCY=="),
        dataSource = dataSource,
        yAxes = getYAxes(panelConfig),
        id = graph_id,
        timeFrom = "55h"
    )

    errorGraph = Graph(
        title = "Count of error on " + api_endpoint + " endpoint",
        targets = getTargets(customer_id, panelConfig, api_endpoint, "==ERROR=="),
        dataSource = dataSource,
        yAxes = getYAxes(panelConfig),
        id = graph_id
    )

    return [latencyGraph, errorGraph]

# Return each api_endpoint as its own row
def getRows(dataSource, customer_id, panelConfig):

    # final rows array to return
    rows = []

    # get all api_endpoints as separate rows
    api_endpoints = panelConfig["http"]["api_endpoints"]
    for api_endpoint_id in range(len(api_endpoints)):
        row = getGraphs(dataSource, customer_id, panelConfig, api_endpoints[api_endpoint_id], api_endpoint_id + 1)
        # make each api_endpoint its own row
        rows.append(Row(panels = row))

    return rows

def create_dashboard(data):
    dashboard_title = data["title"]
    dashboard_rows = getRows(
        data["datasource"],
        data["customer_id"],
        data["panels"]
    )

    return Dashboard(
        title=dashboard_title,
        rows=dashboard_rows
    )

def generate_dashboard_file():
    with open('script/config.json') as json_data_file:
        data = json.load(json_data_file)
    return create_dashboard(data)

"""Entry point for generate-dashboard"""
dashboard = generate_dashboard_file()