import json
from pprint import pprint


def do():
    with open("iron.pal") as f:
        schema = [[int(y) for y in x.split(",")] for x in f.read().split()]
    print(schema)
    with open("pano-20200107162200/info.json") as f:
        info = json.loads(f.read())
        pprint(info)
        highest = info["highestTemperatures"]
        lowest = info["lowestTemperatures"]

do()



"""given color get temperature for each image based on each image's scale"""

"""get global highest and lowest and create the global scale """

"""given a temp gives a color based on the global scale"""

"""
20.9 = [16, 101, 140]
31.3 = [235, 121, 130]

"""
