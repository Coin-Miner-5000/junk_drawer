import hashlib
import requests
import time
import os
import sys

from graph import graph_of_map
from excluded import excluded
from uuid import uuid4

from timeit import default_timer as timer

import random

if __name__ == '__main__':
    node = "https://lambda-treasure-hunt.herokuapp.com/api/adv"
    opposites = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}
    path = []
    graph = excluded
    last_room = None

    # KEY = os.environ.get("API_KEY")
    headers = {'Content-Type': 'application/json',
               'Authorization': "Token "}
    r = requests.get(url=node + "/init", headers=headers)

    def recall():
        r = requests.post(url=node + "/recall", headers=headers)
        data = r.json()
        print('recall data', data)
        print(f"{data.get('cooldown')} second cooldown")
        time.sleep(data.get('cooldown'))
        print('Recall')
        return data

    while True:
        data = r.json()

        time.sleep(data.get('cooldown'))
        exits = data.get('exits')
        room_id = data.get('room_id')
        room_name = data.get('title')
        print('Room ID: ', room_id)
        print('Room Name: ', room_name)

        if len(data.get('items')) > 0:
            time.sleep(data.get('cooldown'))
            r = requests.get(url=node + "/init", headers=headers)
            items_data = r.json()
            items = items_data.get('items')
            print('items in room', items)
            time.sleep(items_data.get('cooldown'))
            for item in items:
                r = requests.post(url=node + "/take",
                                  json={"name": item}, headers=headers)
                take_data = r.json()
                time.sleep(take_data.get('cooldown'))
            r = requests.post(url=node + "/status", headers=headers)
            status_data = r.json()
            print('status data', status_data)
            time.sleep(status_data.get('cooldown'))
            strength = status_data.get('strength')
            encumbrance = status_data.get('encumbrance')
            if encumbrance >= strength:
                recall()
                last_room = items_data.get('room_id')
                path = []
                # graph = init_graph()
                graph = excluded
                r = requests.post(url=node + "/fly", json={
                    "direction": "w", "next_room_id": "1"}, headers=headers)
                shop_data = r.json()
                path.append('w')
                time.sleep(shop_data.get('cooldown'))
                inventory = status_data.get('inventory')
                for item in inventory:
                    r = requests.post(
                        url=node + "/sell", json={"name": item, "confirm": "yes"}, headers=headers)
                    sell_data = r.json()
                    print('just sold ', item)
                    time.sleep(sell_data.get('cooldown'))

        if room_id not in graph:
            graph[room_id] = {"title": data.get('title'), "description": data.get('description'), "terrain": data.get(
                'terrain'), "coordinates": data.get('coordinates'), "elevation": data.get('elevation')}
            for dir in exits:
                graph[room_id][dir] = "?"
        if last_room != None:
            graph[last_room][path[-1]] = room_id
            graph[room_id][opposites[path[-1]]] = last_room
        unexploredExits = [dir for dir in exits if graph[room_id][dir] == "?"]
        print('unexplored exits', unexploredExits)
        if not len(unexploredExits):
            if len(path) == 0:
                print('Final graph')
                print(graph)
                break
            wayBack = opposites[path.pop()]
            r = requests.post(url=node + "/fly", json={
                              "direction": wayBack, "next_room_id": str(graph[room_id][wayBack])}, headers=headers)

            print("Used Wise Explorer")
            last_room = None
        else:
            wayForward = unexploredExits[0]
            path.append(wayForward)
            last_room = room_id
            r = requests.post(url=node + "/fly",
                              json={"direction": wayForward, "next_room_id": str(graph_of_map[room_id][wayForward])}, headers=headers)
            data = r.json()
            print(data.get('cooldown'))
