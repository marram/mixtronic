import json

fh = open("countries.json", "r")
data = json.load(fh).pop()
fh.close()

output = {}
print data
for country in data:
    output[country.get("iso2Code")] = dict(name=country.get("name"), longitude=country.get("longitude"), latitude=country.get("latitude"))

fh = open("country_coordinates.json", "w")
json.dump(output, fh)
fh.close()
print output


fh = open("states.json", "r")
lines = fh.readlines()
fh.close()

output = {}
for line in lines:
    state, lat, lon = line.strip().split(",")
    output[state] = dict(latitude=lat, longitude=lon)
fh = open("states.json", "w")
json.dump(output, fh)
fh.close()
