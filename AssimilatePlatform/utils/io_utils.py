import os, json, datetime, shutil

def now():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_config_any(path):
    """
    Load config from YAML or JSON.
    - If YAML is requested but PyYAML is not installed, raise a helpful error
      (so JSON & interactive modes still work without yaml dependency).
    """
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as f:
        if ext in (".yaml", ".yml"):
            try:
                import yaml  # ← lazy import; only when actually reading YAML
            except Exception as e:
                raise RuntimeError(
                    "YAML config provided but PyYAML is not installed.\n"
                    "Install with:  conda install pyyaml  (or)  pip install pyyaml\n"
                    "Alternatively, use a JSON config or run interactive mode."
                ) from e
            return yaml.safe_load(f)
        else:
            return json.load(f)

def copy_file(src, dst_dir):
    if src and os.path.exists(src):
        shutil.copy2(src, os.path.join(dst_dir, os.path.basename(src)))