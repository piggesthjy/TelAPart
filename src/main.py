import json
from data_preprocessing import data_preprocessing
from issue_detector import detect_maintenance_issue

data_path = "./BENDOR04cmt44.json"
config_path = "./config"


if __name__ == '__main__':
    with open(config_path) as infile:
        configuration = json.loads(infile.read())
    window_size = configuration["window_size"]
    maintenance_threshold = configuration["maintenance_threshold"]
    print("Window Size = %d Days" % window_size)
    print("Maintenance Issue Group Size = %d Modems" % maintenance_threshold)
    
    fns_new, fn_interfaces, max_timestamp = data_preprocessing(data_path)
    left = max_timestamp - window_size * 3600*24 - 3600*4
    right = max_timestamp

    fn_results = {}
    for fn in fns_new:
        detected_issues = detect_maintenance_issue(fns_new[fn], list(fn_interfaces[fn]), left, right, configuration, window_size, maintenance_threshold)
        fn_results.setdefault(fn, detected_issues)
        
    print(json.dumps(fn_results))
