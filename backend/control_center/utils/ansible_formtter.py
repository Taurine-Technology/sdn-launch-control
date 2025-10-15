import re
import logging

logger = logging.getLogger(__name__)


def get_interfaces_from_results(results):
    interfaces = []
    
    # Navigate to the relevant results dictionary
    command_key = "Run ip link show command"
    if results.get('results') and command_key in results['results']:
        output_lines = results['results'][command_key].get('stdout_lines', [])

        for line in output_lines:
            match = re.match(r"^\d+: ([^:@]+)", line)
            if match:
                interfaces.append(match.group(1))  # Extract the interface name

    return interfaces


def get_filtered_interfaces(results):
    """
    Return a list of network interface names extracted from Ansible playbook results, excluding loopback, veth, bridge, and docker interfaces.
    
    Parameters:
        results (dict): Ansible playbook result dictionary that contains a 'results' mapping with the key "Run ip link show command with shell" whose value provides 'stdout_lines' from an `ip link` command.
    
    Returns:
        list: Interface names (str) parsed from the command output, excluding names that start with "lo", "veth", "br-" or equal "docker0".
    """
    interfaces = []
    
    # Define interfaces to exclude (e.g., loopback, bridges, virtual interfaces)
    exclude_patterns = re.compile(r"^(lo|veth.*|br-.*|docker0)$")

    # Navigate to the relevant results dictionary
    command_key = "Run ip link show command with shell"
    if results.get('results') and command_key in results['results']:
        output_lines = results['results'][command_key].get('stdout_lines', [])

        for line in output_lines:
            # print(line)
            match = re.match(r"^\d+: ([^:@]+)", line)  # Extracts interface names
            if match:
                interface_name = match.group(1)
                if not exclude_patterns.match(interface_name):  # Apply filtering
                    interfaces.append(interface_name)

    return interfaces


def get_interface_speeds_from_results(results):
    """
    Extracts interface speeds from Ansible playbook results.
    
    Parameters:
        results (dict or mapping): Either the full playbook result dictionary (containing a 'results' key)
            or the already-extracted results mapping that includes the "Get interface speeds from sysfs"
            task entry. The function accepts either form and normalizes internally.
    
    Returns:
        dict: Mapping of interface name to speed in megabits per second (int), e.g. {'eth0': 1000}.
            Returns an empty dict if no valid speeds are found.
    """
    speeds = {}
    
    # Handle both calling patterns: 
    # 1. Full result dict (has 'results' key)
    # 2. Just the results portion (already extracted)
    results_data = results.get('results', results) if isinstance(results, dict) else results
    
    # Navigate to the relevant results dictionary
    command_key = "Get interface speeds from sysfs"
    
    # Debug: Log available keys to help troubleshooting
    if isinstance(results_data, dict):
        logger.debug(f"Available keys in results_data: {list(results_data.keys())}")
    
    if command_key in results_data:
        output_lines = results_data[command_key].get('stdout_lines', [])
        logger.debug(f"Found {len(output_lines)} lines from speed task")
        
        for line in output_lines:
            if ':' in line:
                parts = line.split(':')
                if len(parts) == 2:
                    iface, speed = parts[0].strip(), parts[1].strip()
                    try:
                        speeds[iface] = int(speed)
                    except ValueError:
                        logger.warning(f"Invalid speed value for {iface}: {speed}")
    
    logger.debug(f"Extracted interface speeds: {speeds}")
    return speeds


def extract_ovs_port_map(playbook_result):
    """
    Extract the Open vSwitch port map mapping interface names to ofport numbers from a playbook result.
    
    Parameters:
        playbook_result (dict): Result returned by run_playbook_with_extravars; expected to contain a 'status' key and a 'results' dictionary.
    
    Returns:
        dict: Mapping of interface name (str) to ofport number (int) if found and valid, otherwise an empty dict.
    """
    ovs_map = {}
    if not isinstance(playbook_result, dict):
        logger.error("Invalid playbook_result format: Expected a dictionary.")
        return ovs_map # Return empty dict

    if playbook_result.get('status') != 'success':
        error_detail = playbook_result.get('error', 'No error details available')
        logger.warning(f"Playbook execution was not successful. Error: {error_detail}")
        logger.warning(f"Full playbook result: {playbook_result}")
        return ovs_map # Return empty dict

    results_data = playbook_result.get('results')
    if not isinstance(results_data, dict):
        logger.warning("Playbook result missing 'results' dictionary.")
        return ovs_map # Return empty dict

    # --- Attempt 1: Extract from the debug task output (Preferred) ---
    try:
        # Ensure the task name matches exactly what's in the playbook's debug task
        debug_task_name = 'Show assembled OVS port map'
        debug_output = results_data.get(debug_task_name, {})
        if isinstance(debug_output, dict):
            potential_map = debug_output.get('ovs_port_map')
            if isinstance(potential_map, dict):
                # Basic validation: keys are strings, values are integers
                if all(isinstance(k, str) and isinstance(v, int) for k, v in potential_map.items()):
                    logger.info(f"Successfully extracted ovs_port_map from debug task: {potential_map}")
                    return potential_map
                else:
                    logger.warning("Map found in debug task has invalid key/value types.")

    except Exception as e:
        logger.warning(f"Error accessing debug task output for ovs_port_map: {e}", exc_info=True)


    # --- Attempt 2: Extract from the set_fact task output (Fallback) ---
    try:
        # Ensure the task name matches exactly what's in the playbook's set_fact task
        set_fact_task_name = 'Assemble port map'
        set_fact_output = results_data.get(set_fact_task_name, {})
        if isinstance(set_fact_output, dict):
            loop_results = set_fact_output.get('results', [])
            if isinstance(loop_results, list) and loop_results:
                # The final map is in the 'ansible_facts' of the last item
                last_item = loop_results[-1]
                if isinstance(last_item, dict):
                    ansible_facts = last_item.get('ansible_facts', {})
                    if isinstance(ansible_facts, dict):
                        potential_map = ansible_facts.get('ovs_port_map')
                        if isinstance(potential_map, dict):
                            # Basic validation
                            if all(isinstance(k, str) and isinstance(v, int) for k, v in potential_map.items()):
                                logger.info(f"Successfully extracted ovs_port_map from set_fact task: {potential_map}")
                                return potential_map
                            else:
                                logger.warning("Map found in set_fact task has invalid key/value types.")

    except Exception as e:
        logger.warning(f"Error accessing set_fact task output for ovs_port_map: {e}", exc_info=True)


    # --- Attempt 3: Check if it exists at the top level of results (Less likely) ---
    # Sometimes facts might appear directly under results if not registered in a loop/task var
    try:
        potential_map = results_data.get('ovs_port_map')
        if isinstance(potential_map, dict):
            if all(isinstance(k, str) and isinstance(v, int) for k, v in potential_map.items()):
                logger.info(f"Successfully extracted ovs_port_map from top-level results: {potential_map}")
                return potential_map
            else:
                logger.warning("Map found in top-level results has invalid key/value types.")
    except Exception as e:
        logger.warning(f"Error accessing top-level results for ovs_port_map: {e}", exc_info=True)

    logger.warning("Could not find 'ovs_port_map' in any expected location within the playbook results.")
    return ovs_map  # Return empty dict if not found