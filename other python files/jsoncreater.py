import json

ag = [13]
ag.append(8)

print(ag)

data = {
    "Name": "Ivan",
    "age": ag,
    "city": "Moscow"
}

json_data = json.dumps(data)




dta = json.loads(json_data)

print(dta["city"])
print(dta["age"][0])



data2 = {
    "num": [{"FH": ["123", "32"], "Links": [1,2,3]}]
}

json_data2 = json.dumps(data2)
#print(json_data2)

dta2 = json.loads(json_data2)

print(dta2)
print(dta2["num"][0]["FH"])

for oc in dta2["num"]:
    for oc2 in oc["FH"]:
        print(oc2)






blocks = ["5368778767", "5368804384"]
opcodes2 = "jmp 0x140017420; "
hashopcodes2 = "3:gvWzVLT:gvmLT; "



dts= {}

item = {}
item['blocks'] = blocks
item["opcodes"] = opcodes2
item["hashopcodes"] = hashopcodes2


dts = item

jsndts = json.dumps(dts)
print(jsndts)



