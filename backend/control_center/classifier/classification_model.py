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
from utils.ip_lookup_service import get_asn_from_ip

columns = ["label"]
# data = ['AmazonAWS', 'Apple', 'Cloudflare', 'Cybersec', 'Facebook', 'GMail', 'Google', 'GoogleCloud', 'GoogleDocs',
#         'GoogleServices', 'HTTP', 'Instagram', 'Microsoft', 'Snapchat', 'Spotify', 'TLS', 'TikTok', 'Twitter',
#         'Unknown', 'WhatsApp', 'WhatsAppFiles', 'Xiaomi', 'YouTube']
data = ["ADS_Analytic_Track", "AmazonAWS", "BitTorrent", "Facebook", "FbookReelStory", "GMail", "Google",
                  "GoogleServices", "HTTP", "HuaweiCloud", "Instagram", "Messenger", "Microsoft", "NetFlix",
                  "QUIC", "TikTok", "TLS", "Unknown", "WhatsApp", "WhatsAppFiles", "WindowsUpdate", "YouTube"]
label_df = pd.DataFrame(data=data, columns=columns)


class ClassificationModel(object):

    def __init__(self, model_file, num_categories, labels=label_df):
        print('importing')
        try:
            self.model = keras.models.load_model(model_file)
            print('model loaded')
            print(self.model.summary())
            last_layer = self.model.layers[-1]
            print(f"Output activation: {last_layer.activation.__name__}")
            self.labels = labels
            label_map = dict(enumerate(self.labels['label'].astype('category').cat.categories))
            self.class_names = [label_map[i] for i in range(num_categories)]

        except Exception as e:
            print(e)
            print('ERROR')
            time.sleep(5)

    def predict_flow(self, packet_arr, client_ip_address=None):
        start_time = time.time()
        packet_array = np.array(packet_arr).reshape(-1, 225, 5)
        x_test = packet_array.astype(int) / 255
        predictions = self.model.predict(x_test)
        y_prediction = np.argmax(predictions)
        end_time = time.time()
        time_elapsed = end_time - start_time
        
        # Get the probabilities for the first (and only) prediction
        probabilities = predictions[0] if len(predictions.shape) > 1 else predictions
        
        # Log top 5 classification percentages
        print("**********************************************")
        print("Top 3 Classification Percentages:")
        print("**********************************************")
        
        # Create list of (class_name, probability) tuples and sort by probability
        class_probabilities = list(zip(self.class_names, probabilities))
        class_probabilities.sort(key=lambda x: x[1], reverse=True)
        
        # Print top 3
        for i, (class_name, probability) in enumerate(class_probabilities[:3]):
            percentage = probability * 100
            print(f"{i+1}. {class_name}: {percentage:.2f}%")
        
        print("**********************************************")
        
        # Confidence and multiple candidate detection
        max_probability = class_probabilities[0][1]
        second_highest_probability = class_probabilities[1][1] if len(class_probabilities) > 1 else 0
        
        # Check confidence thresholds
        high_confidence = max_probability > 0.7
        low_confidence = max_probability < 0.5
        
        # Check for multiple candidates (similar high probabilities)
        # Consider multiple candidates if the difference between top 2 is less than 0.2
        multiple_candidates = (max_probability - second_highest_probability) < 0.2 and second_highest_probability > 0.3
        
        # Determine final prediction
        if high_confidence and not multiple_candidates:
            final_prediction = self.class_names[y_prediction]
            confidence_level = "HIGH"
        else:
            final_prediction = "unable_to_classify"
            if low_confidence:
                confidence_level = "LOW"
            elif multiple_candidates:
                confidence_level = "MULTIPLE_CANDIDATES"
            else:
                confidence_level = "UNCERTAIN"
        
        print(f"Max Probability: {max_probability:.3f}")
        print(f"Second Highest: {second_highest_probability:.3f}")
        print(f"Confidence Level: {confidence_level}")
        print(f"Final Prediction: {final_prediction}")
        print("************************************************")

        if final_prediction == "QUIC":
            try:
                asn_info = get_asn_from_ip(client_ip_address)
                if asn_info:
                    print("*******************QUIC***************************")
                    print("ASN Lookup Results (QUIC):")
                    print(f"Client IP: {client_ip_address}")
                    print(f"ASN: {asn_info['asn']}")
                    print(f"Organization: {asn_info['organization']}")
                    print("*******************QUIC***************************")
                    # For now, just log the ASN information
                    # TODO: Implement ASN-based classification logic
                else:
                    print(f"ASN lookup failed for IP: {client_ip_address}")
            except Exception as e:
                print(f"Error during ASN lookup for IP {client_ip_address}: {e}")
        
        # If not high confidence and we have a client IP address, try ASN lookup
        if not high_confidence or multiple_candidates and client_ip_address:
            try:
                asn_info = get_asn_from_ip(client_ip_address)
                if asn_info:
                    print("**********************************************")
                    print("ASN Lookup Results (Low Confidence Classification):")
                    print(f"Client IP: {client_ip_address}")
                    print(f"ASN: {asn_info['asn']}")
                    print(f"Organization: {asn_info['organization']}")
                    print("**********************************************")
                    # For now, just log the ASN information
                    # TODO: Implement ASN-based classification logic
                else:
                    print(f"ASN lookup failed for IP: {client_ip_address}")
            except Exception as e:
                print(f"Error during ASN lookup for IP {client_ip_address}: {e}")
        
        return final_prediction, time_elapsed
