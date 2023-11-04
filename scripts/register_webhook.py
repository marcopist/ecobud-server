from ecobud.config import SELF_BASE_URL
from ecobud.connections.tink import register_transaction_webhook

if __name__ == "__main__":
    webhook_url = SELF_BASE_URL + "/tink/webhook"
    print("Webhook URL:", webhook_url)
    resp = register_transaction_webhook(webhook_url=webhook_url)
    print("Response:", resp)
