import json
import os
# 当前Python脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 配置文件的相对路径
CONFIG_FILE = os.path.join(current_dir, "config", "definitions.json")

def load_definitions():
    """ Load trend bar detection rules from JSON config file. """
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

# ✅ Example Usage
if __name__ == "__main__":
    config = load_definitions()
    if config:
        print("✅ Trend Bar Config Loaded Successfully!")
        print(json.dumps(config, indent=4))
