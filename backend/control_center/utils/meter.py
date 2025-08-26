def convert_onos_meter_api_id_to_internal_id(meter_id_str):
    """
    Convert a meter ID from its string representation to a positive integer.

    Mapping Rules:
    - "1" to "9" -> Convert directly to integer
    - "a" to "f" -> Convert to 10-15
    - Numeric IDs "10" and higher -> Apply offset correction (IDs 10+ become ID + 6)
    - "1a" to "1f" -> Convert as hexadecimal (e.g., "1a" becomes 26)
    """
    if meter_id_str.isdigit():
        meter_id = int(meter_id_str)
        if meter_id > 9:
            return meter_id + 6
        return meter_id
    elif len(meter_id_str) == 2 and meter_id_str[0] == '1' and meter_id_str[1].lower() in 'abcdef':
        # Convert strings like "1a" to their hexadecimal value
        return int(meter_id_str, 16)
    elif meter_id_str.isalpha() and len(meter_id_str) == 1:
        # Convert a-f to 10-15
        return 10 + (ord(meter_id_str.lower()) - ord('a'))
    else:
        raise ValueError(f"Unsupported meter ID format: {meter_id_str}")
