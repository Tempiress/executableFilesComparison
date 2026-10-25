import csv
import json
from collections import defaultdict

def recursive_dict():
    return defaultdict(recursive_dict)

log_path = "./results/checkpoints/checkpoint_os.log"

with open(log_path, encoding="utf-8") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    header = next(csv_reader)  # Skip header row

    rows = []
    for row in csv_reader:
        rows.append(row)

    # =================== Group data for LEVEL A: [obfuscation] -> [compare_mode] =============================

    tree = recursive_dict()

    for row in rows:
        # Skip error rows or malformed lines
        if len(row) < 10 or not row[7] or row[7] == 'score' or (len(row) > 14 and row[14].strip() != ''):
            continue

        obfuscation = row[2]   # obfuscation technique (e.g. bcf-ind-cff)
        compare_mode = row[6]  # 'GPU' or 'custom'

        node = tree[obfuscation][compare_mode]

        if 'scores' not in node:
            node['scores'] = []
            node['precisions'] = []
            node['recalls'] = []

        node['scores'].append(float(row[7]))
        node['precisions'].append(float(row[8]))
        node['recalls'].append(float(row[9]))

    # Compute Level A Averages for each Obfuscation x Compare_Mode group
    for obf, cmodes in tree.items():
        for cmode, node in cmodes.items():
            count = len(node['scores'])
            if count > 0:
                node['avg_score'] = round(sum(node['scores']) / count, 4)
                node['avg_precision'] = round(sum(node['precisions']) / count, 4)
                node['avg_recall'] = round(sum(node['recalls']) / count, 4)
                node['sample_count'] = count

                # Clean up raw lists for compact output
                del node['scores']
                del node['precisions']
                del node['recalls']

    # Convert defaultdict to regular dict for JSON serialization
    json_output = json.loads(json.dumps(tree))

    # Save to JSON file for Level A Analysis
    output_json_path = "./results/level_a_obfuscation_analysis.json"
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=4, ensure_ascii=False)

    print(f"[*] Level A Analysis complete! Total Obfuscation Techniques: {len(json_output)}")
    print(f"[*] Results saved to: {output_json_path}")

    # ========================================================================================================
    # ===================Group for [hash_type]================================================================
    tree = recursive_dict()

    for row in rows:
        if row[14] != "":
            continue


        h_type = row[4]
        node = tree[h_type]
        if 'scores' not in node :
            node['scores'] = []
            node['precisions'] = []
            node['recalls'] = []

        node['scores'].append(float(row[7]))
        node['precisions'].append(float(row[8]))
        node['recalls'].append(float(row[9]))

    for htype, data in tree.items():
        node = tree[htype]
        node["avg_score"] = round(sum(node["scores"]) / len(node["scores"]), 5)
        node["avg_precision"] = round(sum(node["precisions"]) / len(node["precisions"]), 5)
        node["avg_recall"] = round(sum(node["recalls"]) / len(node["recalls"]), 5)

        del node["scores"]
        del node["precisions"]
        del node["recalls"]

    #print(tree)

    output_json_path = "./results/level_b_obfuscation_analysis.json"
    json_output = json.loads(json.dumps(tree))
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=4, ensure_ascii=False)


    # =========================== top for obfuscations==================================
    output_json_obf_path = "./results/level_a_obfuscation_analysis.json"
    with open(output_json_obf_path) as csv_obfuscations:
        #csv_reader = csv.reader(csv_obfuscations)
        json_obfuscations = json.load(csv_obfuscations)
        sorted_lines = sorted(json_obfuscations.items(), key=lambda x: x[1]["custom"]["avg_precision"])
        sorted_data = dict(sorted_lines)

    sorted_data_json = json.dumps(sorted_data)
    output_json_obf_data_path = "./results/level_a_data_obfuscation_analysis.json"

    with open(output_json_obf_data_path, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, indent=4, ensure_ascii=False)
        #f.write(sorted_data_json)

        rd = recursive_dict()
        # obf_results = []
        #
        #
        # for obf, data in json_obfuscations.items():
        #     node = rd[obf]
        #
        #     print(row)

