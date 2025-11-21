#!/bin/bash
# /usr/local/bin/check_ovs_flows.sh - Ensure essential OVS flows are always present

# Get bridge name from first argument
BRIDGE="${1}"
if [ -z "${BRIDGE}" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Bridge name is required as first argument" >&2
    exit 1
fi

LOG_FILE="/var/log/ovs_flow_check_${BRIDGE}.log"

# Function to write log messages with a timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "${LOG_FILE}" 2>&1
}

log_message "--- Starting OVS flow verification for bridge '${BRIDGE}' ---"

# --- Define the flows we need to ensure exist ---
# We use cookies as unique identifiers for each flow.
# Flow 1: ARP Handler
FLOW_ARP_COOKIE="0x1000"
FLOW_ARP_RULE="cookie=${FLOW_ARP_COOKIE},priority=100,arp,actions=NORMAL"

# Flow 2: Default Forwarding
FLOW_DEFAULT_COOKIE="0x1001"
FLOW_DEFAULT_RULE="cookie=${FLOW_DEFAULT_COOKIE},priority=1,actions=NORMAL"

# Flow 3: Send to Controller (miss rule)
FLOW_CONTROLLER_COOKIE="0xa"
FLOW_CONTROLLER_RULE="cookie=${FLOW_CONTROLLER_COOKIE},priority=0,actions=CONTROLLER:65535"

# --- Check and Add Logic ---
# Use a single `dump-flows` call for efficiency
CURRENT_FLOWS=$(sudo ovs-ofctl dump-flows ${BRIDGE} -OOpenflow13 2>> "${LOG_FILE}")

# Check for ARP flow
if ! echo "${CURRENT_FLOWS}" | grep -q "cookie=${FLOW_ARP_COOKIE}"; then
    log_message "ARP flow (cookie ${FLOW_ARP_COOKIE}) is MISSING. Re-adding..."
    sudo ovs-ofctl add-flow ${BRIDGE} "${FLOW_ARP_RULE}" -OOpenflow13 >> "${LOG_FILE}" 2>&1
    if [ $? -eq 0 ]; then
        log_message "ARP flow (cookie ${FLOW_ARP_COOKIE}) successfully re-added."
    else
        log_message "ERROR: Failed to re-add ARP flow (cookie ${FLOW_ARP_COOKIE})."
    fi
else
    log_message "ARP flow (cookie ${FLOW_ARP_COOKIE}) is present."
fi

# Check for Default Forwarding flow
if ! echo "${CURRENT_FLOWS}" | grep -q "cookie=${FLOW_DEFAULT_COOKIE}"; then
    log_message "Default flow (cookie ${FLOW_DEFAULT_COOKIE}) is MISSING. Re-adding..."
    sudo ovs-ofctl add-flow ${BRIDGE} "${FLOW_DEFAULT_RULE}" -OOpenflow13 >> "${LOG_FILE}" 2>&1
    if [ $? -eq 0 ]; then
        log_message "Default flow (cookie ${FLOW_DEFAULT_COOKIE}) successfully re-added."
    else
        log_message "ERROR: Failed to re-add Default flow (cookie ${FLOW_DEFAULT_COOKIE})."
    fi
else
    log_message "Default flow (cookie ${FLOW_DEFAULT_COOKIE}) is present."
fi

# Check for Send to Controller flow
if ! echo "${CURRENT_FLOWS}" | grep -q "cookie=${FLOW_CONTROLLER_COOKIE}"; then
    log_message "Controller miss flow (cookie ${FLOW_CONTROLLER_COOKIE}) is MISSING. Re-adding..."
    sudo ovs-ofctl add-flow ${BRIDGE} "${FLOW_CONTROLLER_RULE}" -OOpenflow13 >> "${LOG_FILE}" 2>&1
    if [ $? -eq 0 ]; then
        log_message "Controller miss flow (cookie ${FLOW_CONTROLLER_COOKIE}) successfully re-added."
    else
        log_message "ERROR: Failed to re-add Controller miss flow (cookie ${FLOW_CONTROLLER_COOKIE})."
    fi
else
    log_message "Controller miss flow (cookie ${FLOW_CONTROLLER_COOKIE}) is present."
fi

log_message "--- OVS flow verification complete ---"

