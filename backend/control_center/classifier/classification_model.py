# File: classification_model.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.


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
