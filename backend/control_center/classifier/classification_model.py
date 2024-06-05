import numpy as np
import keras
import time
import pandas as pd

columns = ["label"]
data = ['AmazonAWS', 'Apple', 'Cloudflare', 'Cybersec', 'Facebook', 'GMail', 'Google', 'GoogleCloud', 'GoogleDocs',
        'GoogleServices', 'HTTP', 'Instagram', 'Microsoft', 'Snapchat', 'Spotify', 'TLS', 'TikTok', 'Twitter',
        'Unknown', 'WhatsApp', 'WhatsAppFiles', 'Xiaomi', 'YouTube']
label_df = pd.DataFrame(data=data, columns=columns)


class ClassificationModel(object):

    def __init__(self, model_file, num_categories, labels=label_df):
        print('importing')
        try:
            self.model = keras.models.load_model(model_file)
            self.labels = labels
            label_map = dict(enumerate(self.labels['label'].astype('category').cat.categories))
            self.class_names = [label_map[i] for i in range(num_categories)]

        except Exception as e:
            print(e)
            print('ERROR')
            time.sleep(5)

    def predict_flow(self, packet_arr):
        start_time = time.time()
        packet_array = np.array(packet_arr).reshape(-1, 225, 5)
        x_test = packet_array.astype(int) / 255
        y_prediction = np.argmax(self.model.predict(x_test))
        end_time = time.time()
        time_elapsed = end_time - start_time
        # print("**********************************************")
        # print(self.class_names[y_prediction])
        # print("************************************************")
        return self.class_names[y_prediction], time_elapsed
