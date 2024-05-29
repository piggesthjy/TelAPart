import warnings
import numpy as np
import networkx as nx
from scipy.stats import pearsonr
import community as community_louvain
from data_preprocessing import data_preprocessing
warnings.filterwarnings("ignore")

error_reason = ["Tx Power", "SNR", "Missing"]

def align_data(interfaces1, interfaces2):
    interface_list = [interface for interface in interfaces1]
    interface = interface_list[0]
    a = [item[0] for item in interfaces1[interface]]
    b = [item[0] for item in interfaces2[interface]]
    aa = []
    bb = []
    index = 0
    for i in range(len(a)):
        while True:
            if index == len(b)-1:
                break
            else:
                if abs(a[i]-b[index]) > abs(a[i]-b[index+1]):
                    index += 1
                else:
                    break
        aa.append(index)
    index = 0
    for i in range(len(b)):
        while True:
            if index == len(a)-1:
                break
            else:
                if abs(b[i]-a[index]) > abs(b[i]-a[index+1]):
                    index += 1
                else:
                    break
        bb.append(index)
    vector = []
    for i in range(len(aa)):
        if i == bb[aa[i]]:
            vector.append([i, aa[i]])
    a = [item[0] for item in vector][1:]
    b = [item[1] for item in vector][1:]
    return a, b

def detect_maintenance_issue(mids_raw, interface_group, left, right, configuration, window_size, maintenance_threshold):
    interface_group.sort()

    mids = {}
    invalid_mids = []
    for mid in mids_raw:
        data_point_count = 0
        mids.setdefault(mid, {})
        for interface in mids_raw[mid]:
            mids[mid].setdefault(interface, [])
            for item in mids_raw[mid][interface]:
                if left <= item[0] <= right:
                    mids[mid][interface].append(item)
                    if item[1] == 1:
                        data_point_count += 1
        if data_point_count < len(interface_group) * 3 * window_size + 1:
            invalid_mids.append(mid)
    for mid in invalid_mids:
        del mids[mid]
    mid_list = [mid for mid in mids]


    mids_data_to_detect = {}
    for mid in mid_list:
        mids_data_to_detect.setdefault(mid, [[], [], []])
        for interface in interface_group:
            mids_data_to_detect[mid][0].append([])
            mids_data_to_detect[mid][1].append([])
            mids_data_to_detect[mid][2].append([])
            
            for item in mids[mid][interface]:
                mids_data_to_detect[mid][2][-1].append(item[1])
                if item[1] == 1:
                    if isinstance(item[2][3], float):
                        mids_data_to_detect[mid][0][-1].append(item[2][3])
                    else:
                        mids_data_to_detect[mid][0][-1].append(None)
                    if isinstance(item[2][5], float):
                        mids_data_to_detect[mid][1][-1].append(item[2][5])
                    else:
                        mids_data_to_detect[mid][1][-1].append(None)
                else:
                    mids_data_to_detect[mid][0][-1].append(None)
                    mids_data_to_detect[mid][1][-1].append(None)
            

    matrix = [[0] * len(mid_list) for _ in range(len(mid_list))]
    for i in range(len(mid_list)):
        for j in range(i + 1, len(mid_list)):
            mid1 = mid_list[i]
            mid2 = mid_list[j]
            a, b = align_data(mids[mid1], mids[mid2])
            matrix[i][j] = [a, b]
            matrix[j][i] = [b, a]


    similarity_matrix_txpower = [[None] * len(mid_list) for _ in range(len(mid_list))]
    similarity_matrix_snr = [[None] * len(mid_list) for _ in range(len(mid_list))]
    similarity_matrix_missing = [[None] * len(mid_list) for _ in range(len(mid_list))]
    similaritys = [similarity_matrix_txpower, similarity_matrix_snr, similarity_matrix_missing]
    for i in range(len(mid_list)):
        for j in range(i + 1, len(mid_list)):
            mid1 = mid_list[i]
            mid2 = mid_list[j]
            interfaces1 = mids[mid1]
            interfaces2 = mids[mid2]
            a, b = matrix[i][j]
            vector1 = [[], [], []]
            vector2 = [[], [], []]
            for interface in interface_group:
                for k in range(len(a)):
                    x = a[k]
                    y = b[k]
                    missing1 = 0 if interfaces1[interface][x][1] == -1 else 1
                    missing2 = 0 if interfaces2[interface][y][1] == -1 else 1
                    vector1[2].append(missing1)
                    vector2[2].append(missing2)
                break

            for interface in interface_group:
                for k in range(len(a)):
                    x = a[k]
                    y = b[k]
                    if interfaces1[interface][x][1] == 1 and interfaces2[interface][y][1] == 1 and interfaces1[interface][x][2][3] is not None and interfaces2[interface][y][2][3] is not None:
                        vector1[0].append(interfaces1[interface][x][2][3])
                        vector2[0].append(interfaces2[interface][y][2][3])

                    if interfaces1[interface][x][1] == 1 and interfaces2[interface][y][1] == 1 and interfaces1[interface][x][2][5] is not None and interfaces2[interface][y][2][5] is not None:
                        vector1[1].append(interfaces1[interface][x][2][5])
                        vector2[1].append(interfaces2[interface][y][2][5])
            for k in range(3):
                vector1_small = vector1[k]
                vector2_small = vector2[k]

                if k == 2:
                    if len(vector1_small) < window_size*6 - 1:
                        similarity = None
                    else:
                        a = b = 0
                        for kk in range(len(vector1_small)):
                            if vector1_small[kk] == vector2_small[kk]:
                                a += 1
                            else:
                                b += 1
                        similarity = a/(a+b)
                else:
                    if len(vector1_small) < len(interface_group) * 3 * window_size:
                        similarity = None
                    else:
                        similarity = pearsonr(vector1_small, vector2_small)[0]
                        if np.isnan(similarity):
                            similarity = None

                similaritys[k][i][j] = similarity
                similaritys[k][j][i] = similarity


    all_issues = []
    errored_mids = set([])
    for k in range(3):
        G = nx.Graph()
        G.add_nodes_from(mid_list)
        for i in range(len(mid_list)):
            for j in range(i+1, len(mid_list)):
                mid1 = mid_list[i]
                mid2 = mid_list[j]
                similarity = similaritys[k][i][j]
                if similarity is not None and similarity >= configuration["abnormal_thresholds"][error_reason[k]][0]:
                    G.add_edge(mid1, mid2)
        result = community_louvain.best_partition(G)
        labels = [result[mid] for mid in mid_list]
        
        partitions = {}
        clusters = {}
        for i in range(len(labels)):
            label = labels[i]
            partitions.setdefault(mid_list[i], int(label))
            if label not in clusters:
                clusters.setdefault(label, [])
            clusters[label].append(mid_list[i])
            
        for cluster in clusters:
            normal_count = abnormal_count = 0
            for mid in clusters[cluster]:
                if error_reason[k] == "Missing":
                    if mids_data_to_detect[mid][k][-1][-1] == -1:
                        abnormal_count += 1
                    else:
                        normal_count += 1
                else:
                    values_all_channels = mids_data_to_detect[mid][k]
                    abnormal = False
                    for values_in_one_channel in values_all_channels:
                        if values_in_one_channel[-1] is None:
                            continue
                        values_valid = [value for value in values_in_one_channel if value is not None]
                        var = np.var(values_valid)
                        value = values_valid[-1]
                        min_value = max(values_valid) - value
                        for metric, threshold in configuration["abnormal_thresholds"][error_reason[k]][2]:
                            if metric == 'min':
                                if min_value > threshold:
                                    abnormal = True
                                    break
                            elif metric == 'var':
                                if var > threshold:
                                    abnormal = True
                                    break
                            elif metric == 'less':
                                if value < threshold:
                                    abnormal = True
                                    break
                    if abnormal:
                        abnormal_count += 1
                    else:
                        normal_count += 1
            if abnormal_count/(abnormal_count+normal_count) >= configuration["abnormal_thresholds"][error_reason[k]][1]:
                if len(clusters[cluster]) >= maintenance_threshold:
                    all_issues.append([clusters[cluster], "Maintenance", error_reason[k]])
                else:
                    if error_reason[k] != "Missing":
                        all_issues.append([clusters[cluster], "Service", error_reason[k]])
                for mid in clusters[cluster]:
                    errored_mids.add(mid)
    listx = []
    for mid in mid_list:
        if mid not in errored_mids:
            listx.append(mid)
    all_issues.append([listx, "No Issue", "No Issue"])

    return all_issues
