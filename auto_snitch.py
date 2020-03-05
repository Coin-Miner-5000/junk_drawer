from graph import graph_of_map
from underworld_graph import underworld_graph
# from underworld_graph import underworld_graph as graph_of_map
import requests
import sys
import time
import os
from scratch import excluded_rooms

current_world = "overworld"
if current_world == "underworld":
    map_graph = underworld_graph
else:
    map_graph = graph_of_map


def BFS(current_room, destination_room):
    directions = [[]]  # Queue of paths
    room_ids = []  # Queue
    visited = set()
    # room we are searching for

    did_find_room = False

    room_ids.append([current_room])

    while did_find_room == False and len(room_ids) > 0:
        path = room_ids.pop(0)
        node = path[-1]
        added_path = directions.pop(0)

        if node not in visited:
            visited.add(node)
            exits = []
            for dir in ["n", "s", "e", "w"]:
                if dir in map_graph[node]:
                    exits.append(dir)

            for dir in exits:
                next_room = map_graph[node][dir]
                if next_room not in visited and did_find_room == False:
                    new_path = path.copy()
                    next_added_path = added_path.copy()
                    next_added_path.append(dir)
                    new_path.append(next_room)

                    if next_room == destination_room:
                        did_find_room = True
                        print(next_added_path)
                        return next_added_path
                    else:
                        directions.append(next_added_path)
                        room_ids.append(new_path)


if __name__ == '__main__':
    node = "https://lambda-treasure-hunt.herokuapp.com/api/adv"
    KEY = os.environ.get("API_KEY")
    headers = {'Content-Type': 'application/json',
               'Authorization': f"Token token"}
    r = requests.get(url=node + "/init", headers=headers)

    data = r.json()

    destination_room = sys.argv[1]
    action = None

    if len(sys.argv) > 2:
        action = sys.argv[2]

    def examine():
        # Examine the well for the snitch room #
        r = requests.post(url=node + "/examine",
                          json={"name": "well"}, headers=headers)
        well_data = r.json()
        ls8_instructions = well_data.get('description')
        time.sleep(well_data.get('cooldown'))

        # Send it to the LS8 to be decoded
        r = requests.post("https://afternoon-springs-84709.herokuapp.com/ls8",
                          json={"description": ls8_instructions})

        ls8_data = r.json()
        # print("ls_8 data: ", ls8_data)
        return ls8_data

    def collect_treasure(data):
        opposites = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}
        path = []
        graph = excluded_rooms
        last_room = None
        while True:
            time.sleep(data.get('cooldown'))
            exits = data.get('exits')
            room_id = data.get('room_id')
            room_name = data.get('title')
            print("")
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
                    graph = excluded_rooms

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
                        print(f'{item} SOLD!')
                        time.sleep(sell_data.get('cooldown'))

            if room_id not in graph:
                graph[room_id] = {"title": data.get('title'), "description": data.get('description'), "terrain": data.get(
                    'terrain'), "coordinates": data.get('coordinates'), "elevation": data.get('elevation')}
                for dir in exits:
                    graph[room_id][dir] = "?"
            if last_room != None:
                graph[last_room][path[-1]] = room_id
                graph[room_id][opposites[path[-1]]] = last_room
            unexploredExits = [
                dir for dir in exits if graph[room_id][dir] == "?"]
            print('unexplored exits', unexploredExits)
            if not len(unexploredExits):
                if len(path) == 0:
                    print('Final graph')
                    print(graph)
                    graph = excluded_rooms
                    # continue
                wayBack = opposites[path.pop()]
                r = requests.post(url=node + "/fly", json={
                    "direction": wayBack, "next_room_id": str(graph[room_id][wayBack])}, headers=headers)
                # print(r.json())
                data = r.json()
                print("Used Wise Explorer")
                last_room = None
            else:
                wayForward = unexploredExits[0]
                path.append(wayForward)
                last_room = room_id
                r = requests.post(url=node + "/fly",
                                  json={"direction": wayForward, "next_room_id": str(graph_of_map[room_id][wayForward])}, headers=headers)
                data = r.json()
                print("Cooldown: ", data.get('cooldown'))

    def dash(direction_list, current_room):
        room_id = current_room
        i = 0

        while i < len(direction_list):
            count = 1
            next_room_ids = [map_graph[room_id][direction_list[i]]]

            while (i + count) < len(direction_list) and direction_list[i + count] == direction_list[i]:
                # print(next_room_ids, next_room_ids[-1])
                next_room_ids.append(map_graph[next_room_ids[-1]
                                               ][direction_list[i]])
                count += 1
            res = f"{map_graph[room_id][direction_list[i]]}"
            for room in next_room_ids[1:]:
                res += f",{room}"
            # print(direction_list, i)
            if count > 4:
                print("Dash dash do yo thing")
                r = requests.post(url=node + "/dash", json={
                    "direction": direction_list[i], "next_room_ids": res, "num_rooms": str(count)}, headers=headers)
                i += count
            else:
                print("I believe I can fly")
                r = requests.post(url=node + "/fly", json={
                                  "direction": direction_list[i], "next_room_id": str(map_graph[room_id][direction_list[i]])}, headers=headers)
                i += 1
            data = r.json()
            # print(next_room_ids)
            # print(data)
            print(f"{data.get('cooldown')} second cooldown")
            time.sleep(data.get('cooldown'))
            room_id = data.get("room_id")

    def move_to_room(room, data):
        time.sleep(data.get('cooldown'))
        path = BFS(data.get('room_id'), int(room))
        print(data.get('room_id'))
        dash(path, data.get('room_id'))
        # for dir in path:
        #     r = requests.post(url=node + "/fly", json={"direction": dir, "next_room_id": str(
        #         map_graph[data.get('room_id')][dir])}, headers=headers)
        #     data = r.json()
        #     # print(f"{data.get('cooldown')} second cooldown")
        #     print(f"You are in {data.get('room_id')}")
        #     time.sleep(data.get('cooldown'))

    def recall():
        r = requests.post(url=node + "/recall", headers=headers)
        data = r.json()
        # print('recall data', data)
        print(f"Recalled")
        print(f"{data.get('cooldown')} second cooldown")
        time.sleep(data.get('cooldown'))
        print('done')

        return data

    if action == None:
        move_to_room(destination_room, data)

    elif action == "mine":
        while True:
            time.sleep(data.get('cooldown'))
            data = recall()
            move_to_room(55, data)
            r = requests.post(url=node + "/examine",
                              json={"name": "well"}, headers=headers)
            well_data = r.json()

            ls8_instructions = well_data.get('description')

            r = requests.post("https://afternoon-springs-84709.herokuapp.com/ls8",
                              json={"description": ls8_instructions})

            ls8_data = r.json()
            r = requests.get(url=node + "/init", headers=headers)
            data = r.json()
            print(f"Moving to room {ls8_data.get('room')} to mine. ⛏")
            move_to_room(ls8_data.get('room'), data)

            os.system("python miner.py")
            print("Coin mined! Let's do it again.")
            time.sleep(20)

    elif action == "snitch":
        missed_snitch = False
        while True:
            time.sleep(data.get('cooldown'))
            data = recall()
            map_graph = graph_of_map

            # BUY DONUTS
            s = requests.post(url=node + "/status", headers=headers)
            status_data = s.json()
            time.sleep(status_data.get('cooldown'))
            print(status_data)
            if "sugar_rush" not in status_data:
                if status_data.get("gold") >= 20000:
                    # I'll take you to the donut shop
                    move_to_room(15, data)
                    # buy donut
                    r = requests.post(url=node + "/buy",
                                      json={"name": "donut", "confirm": "yes"}, headers=headers)
                    hurtz_donut = r.json()
                    print("donuts ", hurtz_donut)
                    time.sleep(hurtz_donut.get('cooldown'))
                else:
                    # GO GET TREASURE
                    collect_treasure(data)

            # move to overworld well
            r = requests.get(url=node + "/init", headers=headers)
            data = r.json()
            time.sleep(data.get('cooldown'))
            move_to_room(55, data)

            # LET'S DO THE TIME WARP
            r = requests.post(url=node + "/warp", headers=headers)
            map_graph = underworld_graph
            warp_data = r.json()
            time.sleep(warp_data.get('cooldown'))
            # move_to_room(555, warp_data)

            # ls8_data = r.json()
            if missed_snitch is True:
                # if True:
                ls8_data = examine()
                snitch_room = ls8_data.get("room")
                # print("here", ls8_data)
                while ls8_data.get("room") == snitch_room:
                    # print(snitch_room, ls8_data.get("room"))
                    ls8_data = examine()
            else:
                ls8_data = examine()

            r = requests.get(url=node + "/init", headers=headers)
            data = r.json()
            time.sleep(data.get('cooldown'))

            print(
                f"Moving to room {ls8_data.get('room')} to find the golden snitch. ⛏")
            move_to_room(ls8_data.get('room'), data)
            r = requests.get(url=node + "/init", headers=headers)
            data = r.json()
            time.sleep(data.get('cooldown'))
            if 'golden snitch' in data.get('items'):
                r = requests.post(
                    url=node + "/take", json={"name": "golden snitch"}, headers=headers)
                data = r.json()
                time.sleep(data.get('cooldown'))
                print("")
                print("Mine, snitch.")
                print("")
                missed_snitch = False
            else:
                print("")
                print("Missed the snitch, bitch.")
                print("")
                missed_snitch = True

    elif action == "trans":
        time.sleep(data.get('cooldown'))
        if data.get("room_id") != 495:
            move_to_room(495, data)
        count = 0
        while count < 10:
            r = requests.post(url=node + "/status", headers=headers)
            status_data = r.json()
            print("status_data", status_data)
            time.sleep(status_data.get('cooldown'))

            if len(status_data.get("inventory")) > 0:
                item = status_data.get("inventory")[0]
                print(item)
                if item != "well-crafted boots" or item != "exquisite boots" or item != "exquisite jacket":
                    t = requests.post(url=node + "/transmogrify",
                                      json={"name": item}, headers=headers)
                    trans_data = t.json()
                    print("MESSAGE: ", trans_data)
                    time.sleep(trans_data.get('cooldown'))
                    print(trans_data)
                else:
                    print("You've got something exquisite")
                    sys.exit(1)

            count += 1

    sys.exit(0)
