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
                    logger.debug(f"Successfully extracted ovs_port_map from debug task: {potential_map}")
                    return potential_map
                else:
                    logger.warning("Map found in debug task has invalid key/value types.")

    except Exception as e:
        logger.exception(f"Error accessing debug task output for ovs_port_map: {e}")


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
                                logger.debug(f"Successfully extracted ovs_port_map from set_fact task: {potential_map}")
                                return potential_map
                            else:
                                logger.warning("Map found in set_fact task has invalid key/value types.")

    except Exception as e:
        logger.exception(f"Error accessing set_fact task output for ovs_port_map: {e}")


    # --- Attempt 3: Check if it exists at the top level of results (Less likely) ---
    # Sometimes facts might appear directly under results if not registered in a loop/task var
    try:
        potential_map = results_data.get('ovs_port_map')
        if isinstance(potential_map, dict):
            if all(isinstance(k, str) and isinstance(v, int) for k, v in potential_map.items()):
                logger.debug(f"Successfully extracted ovs_port_map from top-level results: {potential_map}")
                return potential_map
            else:
                logger.warning("Map found in top-level results has invalid key/value types.")
    except Exception as e:
        logger.exception(f"Error accessing top-level results for ovs_port_map: {e}")

    logger.warning("Could not find 'ovs_port_map' in any expected location within the playbook results.")
    return ovs_map  # Return empty dict if not found


def get_single_port_speed_from_results(results, port_name):
    """
    Extract the speed for a specific port from Ansible playbook results.
    
    Parameters:
        results (dict): Ansible playbook result dictionary containing a 'results' mapping
            with the key "Get port speed from sysfs" whose value provides 'stdout'.
        port_name (str): Name of the port to get speed for.
    
    Returns:
        int or None: Port speed in megabits per second, or None if not found or invalid.
    """
    results_data = results.get('results', results) if isinstance(results, dict) else results
    
    command_key = "Get port speed from sysfs"
    
    if command_key in results_data:
        speed_output = results_data[command_key].get('stdout', '').strip()
        if speed_output and speed_output != '':
            try:
                speed = int(speed_output)
                if speed > 0:  # Valid speed (exclude -1 or 0)
                    logger.debug(f"Extracted port speed for {port_name}: {speed} Mb/s")
                    return speed
            except ValueError:
                logger.warning(f"Invalid speed value for {port_name}: {speed_output}")
    
    logger.debug(f"No valid speed found for port {port_name}")
    return None


def get_port_status_from_results(results, port_name):
    """
    Extract the port status (up/down) from Ansible playbook results.
    
    Parameters:
        results (dict): Ansible playbook result dictionary containing a 'results' mapping
            with the key "Get port status using ip link show" whose value provides 'stdout_lines'.
        port_name (str): Name of the port to get status for.
    
    Returns:
        bool or None: True if port is up, False if down, None if status cannot be determined.
    """
    logger.debug(f"[PORT_STATUS] Starting status check for port: {port_name}")
    
    results_data = results.get('results', results) if isinstance(results, dict) else results
    
    command_key = "Get port status using ip link show"
    logger.debug(f"[PORT_STATUS] Looking for command key: {command_key}")
    logger.debug(f"[PORT_STATUS] Available keys in results_data: {list(results_data.keys()) if isinstance(results_data, dict) else 'N/A'}")
    
    if command_key in results_data:
        output_lines = results_data[command_key].get('stdout_lines', [])
        output_str = ' '.join(output_lines) if output_lines else ''
        
        logger.debug(f"[PORT_STATUS] Raw output lines for {port_name}: {output_lines}")
        logger.debug(f"[PORT_STATUS] Raw output string for {port_name}: {output_str}")
        
        # Check if port was not found or doesn't exist
        # ip link show returns error messages when interface doesn't exist
        not_found_conditions = [
            'NOT_FOUND' in output_str,
            not output_lines,
            'does not exist' in output_str.lower(),
            'cannot find device' in output_str.lower(),
            'no such device' in output_str.lower()
        ]
        
        logger.debug(f"[PORT_STATUS] Checking if port {port_name} exists:")
        logger.debug(f"[PORT_STATUS]   - 'NOT_FOUND' in output: {'NOT_FOUND' in output_str}")
        logger.debug(f"[PORT_STATUS]   - output_lines empty: {not output_lines}")
        logger.debug(f"[PORT_STATUS]   - 'does not exist' in output: {'does not exist' in output_str.lower()}")
        logger.debug(f"[PORT_STATUS]   - 'cannot find device' in output: {'cannot find device' in output_str.lower()}")
        logger.debug(f"[PORT_STATUS]   - 'no such device' in output: {'no such device' in output_str.lower()}")
        
        if any(not_found_conditions):
            logger.debug(f"[PORT_STATUS] Port {port_name} NOT FOUND - returning False")
            logger.warning(f"Port {port_name} not found on device")
            return False  # Interface doesn't exist, so it's down
        
        logger.debug(f"[PORT_STATUS] Port {port_name} exists, parsing output for state and flags")
        
        # Parse ip link show output to find state
        # Example formats:
        # "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000"
        # "2: eth0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000"
        # "2: eth0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state UP group default qlen 1000" (admin up, no carrier)
        for line in output_lines:
            line_lower = line.lower()
            logger.debug(f"[PORT_STATUS] Processing line: {line}")
            
            # Extract flags from angle brackets to check for NO-CARRIER
            has_no_carrier = False
            has_lower_up = False
            flags_list = []
            
            if '<' in line and '>' in line:
                flags_section = line[line.find('<'):line.find('>')+1]
                flags_lower = flags_section.lower()
                flags_list = [f.strip() for f in flags_lower.replace('<', '').replace('>', '').split(',')]
                has_no_carrier = 'no-carrier' in flags_list
                has_lower_up = 'lower_up' in flags_list
                
                logger.debug(f"[PORT_STATUS] Extracted flags for {port_name}: {flags_list}")
                logger.debug(f"[PORT_STATUS]   - has_no_carrier: {has_no_carrier}")
                logger.debug(f"[PORT_STATUS]   - has_lower_up: {has_lower_up}")
            
            # Check for explicit state UP or DOWN
            if 'state up' in line_lower:
                logger.debug(f"[PORT_STATUS] Found 'state up' in line for {port_name}")
                # Even if state is UP, check for NO-CARRIER - this means interface is admin up but has no physical link
                if has_no_carrier:
                    logger.debug(f"[PORT_STATUS] Port {port_name} has state UP but NO-CARRIER flag - returning False")
                    logger.debug(f"Port {port_name} is DOWN (state UP but NO-CARRIER)")
                    return False
                # Also check for LOWER_UP - if state is UP but LOWER_UP is missing, it might not be fully operational
                # However, LOWER_UP can be missing even when interface is up (e.g., some virtual interfaces)
                # So we only return False if we have NO-CARRIER
                logger.debug(f"[PORT_STATUS] Port {port_name} has state UP and no NO-CARRIER - returning True")
                logger.debug(f"Port {port_name} is UP (from state)")
                return True
            elif 'state down' in line_lower:
                logger.debug(f"[PORT_STATUS] Found 'state down' in line for {port_name} - returning False")
                logger.debug(f"Port {port_name} is DOWN (from state)")
                return False
        
        logger.debug(f"[PORT_STATUS] No explicit state found in output, checking flags in angle brackets")
        
        # If no explicit state found, check flags in angle brackets
        # UP flag without NO-CARRIER usually means the interface is up
        # But we need to be careful - LOWER_UP alone doesn't mean the interface is up
        for line in output_lines:
            line_lower = line.lower()
            if '<' in line and '>' in line:
                flags_section = line[line.find('<'):line.find('>')+1]
                flags_lower = flags_section.lower()
                # Split flags and check for exact 'up' flag (not lower_up, upper_up, etc.)
                flags_list = [f.strip() for f in flags_lower.replace('<', '').replace('>', '').split(',')]
                logger.debug(f"[PORT_STATUS] Checking flags for {port_name}: {flags_list}")
                
                # Check for NO-CARRIER first - if present, interface is down
                if 'no-carrier' in flags_list:
                    logger.debug(f"[PORT_STATUS] Port {port_name} has NO-CARRIER flag - returning False")
                    logger.debug(f"Port {port_name} is DOWN (NO-CARRIER flag)")
                    return False
                if 'up' in flags_list:
                    # Check if there's a state mentioned elsewhere in the line
                    if 'state' not in line_lower:
                        logger.debug(f"[PORT_STATUS] Port {port_name} has 'up' flag and no state mentioned - returning True")
                        logger.debug(f"Port {port_name} appears to be UP (from flags)")
                        return True
                    else:
                        logger.debug(f"[PORT_STATUS] Port {port_name} has 'up' flag but state is mentioned in line, skipping flag check")
        
        # If we have output but couldn't determine state, default to None
        logger.debug(f"[PORT_STATUS] Could not determine status for port {port_name} from output - returning None")
        logger.warning(f"Could not determine status for port {port_name} from output: {output_str}")
        return None
    
    logger.debug(f"[PORT_STATUS] Command key '{command_key}' not found in results_data")
    logger.warning(f"Could not find port status task results for {port_name}")
    return None