import json

def data_preprocessing(data_path):
    with open(data_path) as infile:
        metadata = json.loads(infile.read())
    keys = ['@timestamp', 'mac', 'fn', 'freq', 'interface', 'txpower', 'rxpower', 'snr']
    dictx = [{} for _ in range(len(keys))]
    for i in range(len(keys)):
        dictx[i] = metadata[keys[i]]

    fns = {}
    fn_interfaces = {}
    max_timestamp = 0
    for key in dictx[0]:
        values = []
        for i in range(len(dictx)):
            values.append(dictx[i][key])
        timestamp, mid, fn, freq, interface, txpower, rxpower, snr = values
        try:
            txpower = float(txpower)
        except:
            txpower = None
        try:
            rxpower = float(rxpower)
        except:
            rxpower = None
        try:
            snr = float(snr)
        except:
            snr = None

        if fn not in fns:
            fns.setdefault(fn, {})
            fn_interfaces.setdefault(fn ,set([]))
        fn_interfaces[fn].add(interface)
        if mid not in fns[fn]:
            fns[fn].setdefault(mid, [])
        fns[fn][mid].append([int(timestamp/1000), interface, freq, txpower, rxpower, snr])
        max_timestamp = max(int(timestamp/1000), max_timestamp)
    for fn in fns:
        for mid in fns[fn]:
            fns[fn][mid].sort(key=lambda x:x[0])


    fns_new = {}
    for fn in fns:
        interface_group = list(fn_interfaces[fn])
        interface_group.sort()
        if len(interface_group) < 3:
            continue
            
        fns_new.setdefault(fn, {})
        for mid in fns[fn]:
            listx = fns[fn][mid]
            listy = []
            listz = [] 
            interface_set = set([])

            for item in listx:
                interface = item[1]
                interface_set.add(interface)
                if len(listz) == 0 or item[0] - listz[-1][0] < 20:
                    listz.append(item)
                else:
                    listy.append(listz)
                    listz = [item]
            listy.append(listz)
            interface_list = list(interface_set)
            interface_list.sort()

            for i in range(len(listy)):
                visited_interface = set([])
                listx = []
                for item in listy[i]:
                    if item[1] not in visited_interface:
                        visited_interface.add(item[1])
                        listx.append(item)
                listx.sort(key=lambda x:x[2])
                listy[i] = listx

            listx = [[listy[0][0][0], 1, listy[0]]]
            for i in range(1, len(listy)):
                while listy[i][0][0] - listx[-1][0] > 7.01*3600:
                    listx.append([listx[-1][0]+3600*4, 0])
                listx.append([listy[i][0][0], 1, listy[i]])
            while max_timestamp - listx[-1][0] > 7.01*3600:
                listx.append([listx[-1][0]+3600*4, 0])

            if mid not in fns_new[fn]:
                fns_new[fn].setdefault(mid, {})
            for interface in interface_group:
                fns_new[fn][mid].setdefault(interface, [])

            for i in range(len(listx)):
                dictx = {}
                timestamp = listx[i][0]
                tag = -1
                if listx[i][1] == 1:
                    tag = 1
                    for item in listx[i][2]:
                        interface = item[1]
                        dictx.setdefault(interface, item)

                for interface in interface_group:
                    if interface not in dictx:
                        current_tag = 0 if tag == 1 else -1
                        fns_new[fn][mid][interface].append([timestamp, current_tag])
                    else:
                        fns_new[fn][mid][interface].append([timestamp, 1, dictx[interface]])
    return fns_new, fn_interfaces, max_timestamp