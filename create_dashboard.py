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


# getLatencyGraph will return latency graph
def getLatencyGraph(dataSource, customer_id, panelConfig, api_endpoint, graph_id, gridPos):
    return Graph(
        title = "Avg latency on " + api_endpoint + " endpoint",
        targets = getTargets(customer_id, panelConfig, api_endpoint, "==LATENCY=="),
        dataSource = dataSource,
        yAxes = getYAxes(panelConfig),
        id = graph_id,
        timeFrom = "1h",
        gridPos = gridPos
    )


# getErrorGraph will return error graph
def getErrorGraph(dataSource, customer_id, panelConfig, api_endpoint, graph_id, gridPos):
    return Graph(
        title = "Count of error on " + api_endpoint + " endpoint",
        targets = getTargets(customer_id, panelConfig, api_endpoint, "==ERROR=="),
        dataSource = dataSource,
        yAxes = getYAxes(panelConfig),
        id = graph_id,
        timeFrom = "1h",
        gridPos = gridPos
    )


def getDescriptionPanel(graphID, gridPos):
    return Text(
        content = "# Latency for qa-twotwotest on all endpoints can be seen here",
        #height = 5,
        id = graphID,
        links = [],
        mode = TEXT_MODE_MARKDOWN,
        #span = 12,
        title = "",
        transparent = True,
        gridPos = gridPos
        #type = TEXT_TYPE
        #gridPos = gridPos,
        #type = "text"
    )


def getDashlistPanel(graphID, gridPos):
    return Dashlist(
        folderId = None,
        gridPos = gridPos,
        headings = True,
        id = graphID,
        limit = 10,
        links = [],
        query = None,
        recent = False,
        search = True,
        starred = False,
        tags = [],
        title = "Panel Title",
        transparent = True,
        type = "dashlist"
    )

# Return each api_endpoint as its own row
def getPanels(dataSource, customer_id, panelConfig):

    # final rows array to return
    panels = []

    # unique id is needed for each graph
    graphID = 1

    # A panel with description of the dashboard
    gridPos = GridPos(
        h = 5,
        w = 12,
        x = 0,
        y = 0
    )
    descriptionPanel = getDescriptionPanel(graphID, gridPos)
    panels.append(descriptionPanel)

    graphID = graphID + 1
    gridPos = GridPos(
        h = 5,
        w = 12,
        x = 12,
        y = 0
    )
    dashlistPanel = getDashlistPanel(graphID, gridPos)
    panels.append(dashlistPanel)

    # get all api_endpoints as separate rows
    api_endpoints = panelConfig["http"]["api_endpoints"]

    # initial gridPos, which will have to be increamented for each graph's position
    gridPos = GridPos(
        h = 5,
        w = 12,
        x = 0,
        y = 5
    )

    for api_endpoint_id in range(len(api_endpoints)):

        gridPosY = (graphID/2) * gridPos.h

        latencyGridPos = GridPos(5, 12, 0, gridPosY)
        graphID = graphID + 1
        latencyPanel = getLatencyGraph(dataSource, customer_id, panelConfig, api_endpoints[api_endpoint_id], graphID, latencyGridPos)
        panels.append(latencyPanel)
        latencyPanel = []

        errorGridPos = GridPos(5, 12, 12, gridPosY)
        graphID = graphID + 1
        errorPanel = getErrorGraph(dataSource, customer_id, panelConfig, api_endpoints[api_endpoint_id], graphID, errorGridPos)
        panels.append(errorPanel)
        errorPanel = []

    return panels


def create_dashboard(data):
    dashboard_title = data["title"]
    dashboard_panels = getPanels(
        data["datasource"],
        data["customer_id"],
        data["panels"]
    )

    return Dashboard(
        title=dashboard_title,
        rows=[],
        panels=dashboard_panels,
        refresh="30m"
    )


def generate_dashboard_file():
    with open('config.json') as json_data_file:
        data = json.load(json_data_file)
    return create_dashboard(data)


"""Entry point for generate-dashboard"""
dashboard = generate_dashboard_file()
