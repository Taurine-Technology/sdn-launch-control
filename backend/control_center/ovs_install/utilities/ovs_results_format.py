# File: ovs_results_format.py
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

"""
Description:
This script contains utility functions designed for parsing and formatting the results obtained from Ansible playbooks
related to Open vSwitch (OVS) configurations. These functions are essential in interpreting the raw output from OVS
related commands and transforming them into structured data that can be easily understood and used in other parts of
the application.

Functions:
1. format_ovs_show_bridge: Parses the output of the OVS 'show' command to extract details about OVS bridges and their
   associated ports, returning a structured dictionary of this information.
2. format_ovs_get_controller: Parses the output of the OVS 'get-controller' command to extract the controller IP and
   port information for a given OVS bridge, returning this information in a structured format.

These functions are utilized in various parts of the application where processing of Ansible playbook results is required.
"""


def format_ovs_show(results):
    key = 'Get OVS Details'
    target = 'stdout_lines'
    bridges = {}
    bridge_name = None
    num_bridges = 0

    if results.get(key):
        results_dic = results[key]
        show_output = results_dic[target]

        for line in show_output:
            line = line.strip(" ")
            if "Bridge" in line:
                num_bridges += 1
                line = line.split(" ")
                bridge_name = line[-1]
                bridges[bridge_name] = {}
            elif "ovs_version" in line:  # this is the end
                break
            elif "Port" in line:
                line = line.split(" ")
                port_name = line[-1]
                if bridges[bridge_name].get("Ports"):
                    bridges[bridge_name]["Ports"].append(port_name)
                else:
                    bridges[bridge_name]["Ports"] = [port_name]
            elif "Controller" in line:
                line = line.split("\"")
                # print(line)
                controller_info = line[1]
                if bridges[bridge_name].get("Controller"):
                    bridges[bridge_name]["Controller"].append(controller_info)
                else:
                    bridges[bridge_name]["Controller"] = [controller_info]
        return bridges


def format_ovs_get_controller(results):
    key = 'Check Controller for OVS Bridge'
    target = 'stdout'

    if results.get(key):
        results_dic = results[key]
        show_output = results_dic[target]
        show_output_arr = show_output.split(":")
    
        if len(show_output_arr) > 1:
            controller = {'ip': show_output_arr[1], 'port': show_output_arr[2]}
            if len(show_output_arr[2]) > 0:
                return controller
    controller = None
    return controller


def format_ovs_show_bridge_command(results):
    """
    Used to fomat 'ovs-ofctl -O OpenFlow13 show bridge_name'
    :param results:
    :return:
    """
    key = 'Get Bridge DPID and details'
    target = 'stdout'
    bridge_results = {}

    if results.get(key):
        results_dic = results[key]
        # print(f'Dictionary with key {key}')
        # print(results_dic)
        show_output = results_dic[target]
        # print(f'Output with target {target}')
        # print(show_output)
        show_output = show_output.split('\n')
        # print(show_output)
        ofpt_features = show_output[0]
        ofpt_features = ofpt_features.split(' ')
        of_version = ofpt_features[1]
        of_version = of_version.replace("(", "").replace(")", "")
        bridge_results['of_version'] = of_version
        dpid = ofpt_features[3].split(':')[-1]
        bridge_results['dpid'] = dpid
        n_details = show_output[1].split(',')
        n_tables = n_details[0].split(':')[-1]
        n_buffers = n_details[1].split(':')[-1]
        bridge_results['n_tables'] = n_tables
        bridge_results['n_buffers'] = n_buffers
        return bridge_results
    bridge_results = None
    return bridge_results


def format_ovs_dump_flows(results):
    """
    Used to fomat 'ovs-ofctl -OOpenFlow13 --names --no-stat dump-flows {{ bridge_name }}
    :param results:
    :return:
    """
    key = 'Show OVS Dump Flow Details'
    target = 'stdout'
    bridge_results = {}

    if results.get(key):
        results_dic = results[key]
        show_output = results_dic[target]
        show_output = show_output.split('\n')
  
        flows = []
        for row in show_output:
            row_arr = row.split(',')
            flow = {}
            for i in row_arr:
                if 'in_port' in i:
                    
                    flow['in_port'] = i.split('=')[-1]
                elif 'dl_src' in i:
                    
                    flow['dl_src'] = i.split('=')[-1]
                elif 'dl_dst' in i:
                    data = i.split(' ')
                    # Extract dl_dst from the first part
                    dl_dst_val = data[0].split('=')[-1]
                    flow['dl_dst'] = dl_dst_val
                    # Only attempt to extract out_port if the second part exists and contains 'output:'
                    if len(data) > 1 and 'output:' in data[1]:
                        out_port_val = data[1].split('output:')[-1]
                        flow['out_port'] = out_port_val
                    else:
                        # Handle cases where output port info is missing or structured differently
                        flow['out_port'] = None
            if flow:

                flows.append(flow)


        return flows
