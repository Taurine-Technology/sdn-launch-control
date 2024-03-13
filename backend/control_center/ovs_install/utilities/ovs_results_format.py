"""
Author(s): Keegan White
Maintainer: Keegan White
Contact: keeganthomaswhite@gmail.com
Created: Jan 11, 2024
Last Modified: Mar 13, 2024

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
        return bridges


def format_ovs_get_controller(results):
    key = 'Check Controller for OVS Bridge'
    target = 'stdout'

    if results.get(key):
        results_dic = results[key]
        show_output = results_dic[target]
        show_output_arr = show_output.split(":")
        print(show_output_arr)
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
    key = 'Show bridge output'
    target = 'ovs_bridge_output.stdout_lines'
    bridge_results = {}
    if results.get(key):
        results_dic = results[key]
        show_output = results_dic[target]
        # show_output = show_output.split(',')
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
