import os, datetime

def create_result_folder(base_path="./results"):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder = os.path.join(base_path, ts)
    os.makedirs(folder, exist_ok=True)
    return folder