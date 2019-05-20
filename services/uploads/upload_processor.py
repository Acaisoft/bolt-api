from google.cloud import storage
from google.cloud import pubsub_v1


def register_upload_processor(config):
    # get credentials from json file
    credentials = storage.Client()._credentials
    # call at startup to connect to the pubsub subscription in
    sub_client = pubsub_v1.SubscriberClient()
    sub = sub_client.subscription_path(credentials._project_id, config.get('UPLOADS_PUBSUB_SUBSCRIPTION'))
    sub_future = sub_client.subscribe(sub, callback=upload_processor)
    print(sub_future)


def upload_processor(pub_msg):
    print(pub_msg)
