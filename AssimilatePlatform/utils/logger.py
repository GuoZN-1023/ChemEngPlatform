import os, datetime

class Logger:
    def __init__(self, logfile):
        self.file = logfile
        os.makedirs(os.path.dirname(logfile), exist_ok=True)

    def log(self, level, msg):
        line = f"[{level}] {datetime.datetime.now().isoformat()} {msg}\n"
        with open(self.file, "a", encoding="utf-8") as f:
            f.write(line)

    def info(self, msg): self.log("INFO", msg)
    def warn(self, msg): self.log("WARN", msg)
    def error(self, msg): self.log("ERROR", msg)