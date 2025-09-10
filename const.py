DOMAIN = "wattbox_300_700"
PLATFORMS = ["switch", "sensor", "button"]

CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_VERIFY_SSL = "verify_ssl"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_OUTLETS = "outlets"
CONF_MODEL = "model"

DEFAULT_SCAN_INTERVAL = 10
DEFAULT_VERIFY_SSL = True
DEFAULT_MODEL = "WB-700-IPV-12"

# Model → outlet count
MODEL_CHOICES = {
    "WB-300-IP-3": 3,
    "WB-300VB-IP-5": 5,
    "WB-700-IPV-12": 12,
    "WB-700CH-IPV-12": 12,
}

def outlets_for(model: str) -> int:
    return MODEL_CHOICES.get(model, MODEL_CHOICES[DEFAULT_MODEL])
