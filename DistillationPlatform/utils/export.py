import json

def save_results(result, folder):
    with open(f"{folder}/summary.json", "w") as f:
        json.dump(result["summary"], f, indent=4)
    result["data"].to_csv(f"{folder}/results.csv", index=False)