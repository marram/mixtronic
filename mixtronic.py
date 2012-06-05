#!/usr/bin/python
# -*- coding: utf-8 -*-
import settings
from mixpanel import Mixpanel
from datetime import datetime, timedelta
import yaml
from leftronic import Leftronic
import json
import time
import urllib2

class Mixtronic(object):
    @property
    def mixpanel(self):
        return Mixpanel(settings.MIXPANEL_API_KEY, settings.MIXPANEL_API_SECRET)

    @property
    def leftronic(self):
        return Leftronic(settings.LEFTRONIC_ACCESS_KEY)

    def segmentation(self, event, params, endpoints=['segmentation']):
        params['event'] = event
        return self.mixpanel.request(endpoints, params)

    def populate_geo_points(self, stream_name, point_list):
        """ The leftronic API lacks this one.
        """
        return self.leftronic.postData(dict(streamName=stream_name, point=point_list))

def to_leaderboard(mixpanel_output):
    output = list()
    for name, output_dict in mixpanel_output.get("data").get("values").items():
        output.append(dict(zip(["name", "value"], (name, output_dict.values().pop()))))
    return output

def to_graph(mixpanel_output, prefix="$"):
    output = list()
    for key, value in mixpanel_output.get("results").items():
        output.append(dict(prefix=prefix, number=value, timestamp=time.mktime(datetime.strptime(key, "%Y-%m-%d").timetuple())))
        # output.append(dict(x=key, y=value))
    return sorted(output, key=lambda entry: entry.get("timestamp"))

def to_map(country_codes):
    output = list()
    for code, value in country_codes.items():
        coordinates = coordinates_for(code)
        for i in range(0, value):
            output.append(coordinates)
    return output

fh = open("country_coordinates.json", "r")
country_coordinates = json.load(fh)
fh.close()
def coordinates_for_country(country_iso_code):
    country = country_coordinates.get(country_iso_code.upper())
    return dict(longitude=country.get("longitude"), latitude=country.get("latitude"))


fh = open("states.json", "r")
state_coordinates = json.load(fh)
fh.close()
def coordinates_for_state(state_code):
    state = state_coordinates.get(state_code.upper())
    return dict(longitude=state.get("longitude"), latitude=state.get("latitude"))

def coordinates_for(zip_code_or_country_or_state):

    try:
        return coordinates_for_state(zip_code_or_country_or_state)
    except:
        pass
    try:
        return coordinates_for_country(zip_code_or_country_or_state)
    except:
        pass
    url = "http://maps.google.com/maps/geo?q=%s" % str(zip_code_or_country_or_state.upper())
    print url
    response = json.loads(urllib2.urlopen(url).read())
    print response
    coordinates = response.get("Placemark")[0].get("Point").get("coordinates")
    return dict(latitude=coordinates[0], longitude=coordinates[1])

if __name__ == "__main__":
    m = Mixtronic()
    today = datetime.now().date().strftime("%Y-%m-%d")

    mp_data = m.segmentation("Bought Product", dict(from_date=today, to_date=today, on='properties["Name"]'))
    leaderboard = to_leaderboard(mp_data)

    print leaderboard

    # Push it to leftronic.
    print m.leftronic.pushLeaderboard("top_products", leaderboard)

    three_days_ago = (datetime.now() - timedelta(days=3)).date()
    a_week_ago = (datetime.now() - timedelta(days=7)).date()
    mp_data = m.segmentation("Order Placed", dict(from_date=a_week_ago, to_date=today, on='properties["Sub Total"]'), endpoints=['segmentation', 'sum'])

    print mp_data

    graph = to_graph(mp_data)

    print graph

    print m.leftronic.pushNumber("weekly_revenue", graph)

    mp_data = m.segmentation("Order Placed", dict(from_date=today, to_date=today, on='properties["Sub Total"]'), endpoints=['segmentation', 'sum'])

    point = to_graph(mp_data).pop()
    print point
    m.leftronic.pushNumber("revenue_today", point)

    params = dict(from_date=today, to_date=today, on='properties["Sub Total"]')
    params["where"] = '"Eur" == properties["Currency Used"]'
    mp_data = m.segmentation("Order Placed", params, endpoints=['segmentation', 'sum'])
    print mp_data

    m.leftronic.pushNumber("revenue_today_eur", to_graph(mp_data, prefix="€").pop())

    # Get shipments by country
    params = dict(from_date=a_week_ago, to_date=today, on='properties["Shipping Country"]', buckets=1)
    mp_data = m.segmentation("Order Placed", params)

    print mp_data
    m.leftronic.clear("world_shipping")
    # Sum up the data.
    values = mp_data.get("data").get("values")
    data = {}
    for key, series in values.items():
        bin_sum = sum(series.values())
        data[key.upper()] = bin_sum

    world_map = to_map(data)
    m.populate_geo_points("world_shipping", world_map)


    # Get shipments by state
    params = dict(from_date=a_week_ago, to_date=today, on='properties["Shipping State"]')
    params['where'] = '("Us" == properties["Shipping Country"] and "Xx" != properties["Shipping State"])'
    mp_data = m.segmentation("Order Placed", params)

    # Sum up the data.
    values = mp_data.get("data").get("values")
    data = {}
    for key, series in values.items():
        bin_sum = sum(series.values())
        print key
        data[key.upper()] = bin_sum

    print data
    world_map = to_map(data)

    m.populate_geo_points("world_shipping", world_map)
    print world_map



