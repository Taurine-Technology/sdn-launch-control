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

def extract_ovs_port_map(playbook_result):
    """
    Extracts the ovs_port_map dictionary {interface_name: ofport_number}
    from the result of the 'get-ovs-port-numbers' playbook.

    Args:
        playbook_result (dict): The dictionary returned by run_playbook_with_extravars.
                                It's expected to have a 'status' and 'results' key.

    Returns:
        dict: The extracted ovs_port_map, or an empty dict if not found,
              if the playbook failed, or if the result format is unexpected.
    """
    ovs_map = {}
    if not isinstance(playbook_result, dict):
        logger.error("Invalid playbook_result format: Expected a dictionary.")
        return ovs_map # Return empty dict

    if playbook_result.get('status') != 'success':
        logger.warning("Playbook execution was not successful. Cannot extract port map.")
        # Optionally log playbook_result.get('error') if available
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
    return ovs_map # Return empty dict if not found