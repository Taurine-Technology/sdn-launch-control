# SNMP Integration Testing Guide

This guide walks you through testing the SNMP integration implementation step by step.

## Prerequisites

1. **Python Environment**: Ensure your Django backend environment is activated
2. **pysnmp Installed**: Should already be in `requirements.txt` (pysnmp==7.1.22)
3. **SNMP Device**: Access to a device with SNMP enabled (or use an SNMP simulator)

## Step 1: Low-Level SNMP Utilities

### What This Tests

- `get_snmp_value()` - Single SNMP GET operations
- `walk_snmp_table()` - SNMP WALK operations (table retrieval)
- `get_device_metrics()` - Device-level metrics (CPU, memory, uptime)
- `get_interface_statistics()` - Per-interface statistics

### Running the Test

```bash
cd /home/eino/Documents/repos/sdn-launch-control/backend/control_center

# Basic usage
python test_snmp_step1.py <IP_ADDRESS> <COMMUNITY_STRING> [VENDOR]

# Examples:
python test_snmp_step1.py 192.168.1.1 public
python test_snmp_step1.py 10.10.10.6 public mikrotik
python test_snmp_step1.py 10.10.10.10 public ubiquiti
```

### Expected Output

The script will run 4 tests:

1. **get_snmp_value** - Tests basic SNMP GET for system info
   - Should return: system name, uptime, description
   
2. **walk_snmp_table** - Tests SNMP WALK for interfaces
   - Should return: list of network interfaces
   
3. **get_device_metrics** - Tests device-level metric collection
   - Should return: CPU, memory, uptime (vendor-dependent)
   
4. **get_interface_statistics** - Tests interface stats collection
   - Should return: bytes/packets in/out, errors, speed, status

### Success Criteria

✅ **Pass**: All 4 tests pass, output shows:
   - System information retrieved
   - At least 1 interface discovered
   - Device metrics collected (at least uptime)
   - Interface statistics collected

✅ **Partial Pass**: 2-3 tests pass
   - If only uptime works but not CPU/memory → vendor OIDs may need adjustment
   - This is okay to proceed if basic connectivity works

❌ **Fail**: 0-1 tests pass
   - Check device connectivity
   - Verify SNMP is enabled on device
   - Verify community string is correct
   - Check firewall rules

### Common Issues & Solutions

#### Issue: "SNMP error... Timeout"
**Solution**: 
- Check device is reachable: `ping <IP>`
- Verify SNMP is enabled on the device
- Check firewall rules allow UDP port 161

#### Issue: "Authentication failure"
**Solution**:
- Verify the community string is correct
- On MikroTik: `/snmp community print`
- Ensure SNMPv2c is enabled (not just v3)

#### Issue: "No metrics collected" but uptime works
**Solution**:
- This is vendor-specific
- CPU/memory OIDs may need adjustment
- Proceed to next step anyway (basic connectivity works)

#### Issue: "No interfaces found"
**Solution**:
- Device may not support standard interface MIB
- Check device SNMP configuration
- Try with a different device for initial testing

### Example Successful Output

```
======================================================================
  SNMP INTEGRATION - STEP 1 TEST
======================================================================

  Target Device: 10.10.10.6
  Community:     public
  Vendor:        mikrotik

======================================================================

======================================================================
  TEST 1: get_snmp_value() - Single SNMP GET
======================================================================

1. Getting sysName (1.3.6.1.2.1.1.5.0)...
   ✓ Success: pi-switch

2. Getting sysUpTime (1.3.6.1.2.1.1.3.0)...
   ✓ Success: 12345678 (hundredths of seconds)
   → Human readable: 1d 10h 17m

3. Getting sysDescr (1.3.6.1.2.1.1.1.0)...
   ✓ Success: RouterOS RB2011

======================================================================
  TEST 2: walk_snmp_table() - SNMP WALK
======================================================================

1. Walking interface descriptions (1.3.6.1.2.1.2.2.1.2)...
   ✓ Success: Found 8 interfaces
      1. Interface 1: ether1
      2. Interface 2: ether2
      ...

======================================================================
  TEST 3: get_device_metrics() - Device-Level Metrics
======================================================================

1. Collecting metrics for vendor 'mikrotik'...
   ✓ Success: Collected device metrics

   Metrics:
      • CPU Usage:    12.5%
      • Memory Usage: 45.2%
      • Uptime:       123456 seconds
                      (1d 10h 17m)

======================================================================
  TEST 4: get_interface_statistics() - Interface Stats
======================================================================

1. Collecting interface statistics...
   ✓ Success: Collected stats for 8 interfaces

   Interface 1: ether1 (index 1)
      • Bytes In:     1,234,567,890
      • Bytes Out:    987,654,321
      • Packets In:   9,876,543
      • Packets Out:  8,765,432
      • Errors In:    0
      • Errors Out:   0
      • Speed:        1000000000 bps
      • Oper Status:  1 (1=up, 2=down)

======================================================================
  TEST SUMMARY
======================================================================

   ✓ PASS  get_snmp_value
   ✓ PASS  walk_snmp_table
   ✓ PASS  get_device_metrics
   ✓ PASS  get_interface_statistics

   Total: 4/4 tests passed

   🎉 All tests passed! Step 1 is complete.
   You can now proceed to Step 2.

======================================================================
```

## Using an SNMP Simulator (Optional)

If you don't have a physical device, you can use `snmpsim`:

```bash
# Install snmpsim
pip install snmpsim

# Run simulator (in separate terminal)
snmpsimd.py --data-dir=/usr/share/snmpsim/data --agent-udpv4-endpoint=127.0.0.1:1161

# Test against simulator
python test_snmp_step1.py 127.0.0.1 public other
```

Note: The simulator may not have vendor-specific OIDs, so CPU/memory might not work.

## Next Steps

Once Step 1 tests pass:

1. ✅ **Step 1 Complete** - Low-level SNMP utilities work
2. **Step 2** - Implement high-level metric helpers (already done in utilities.py)
3. **Step 3** - Implement `poll_snmp_device()` orchestrator
4. **Step 4** - Implement Celery tasks
5. **Step 5** - Implement API endpoints
6. **Step 6** - Add admin registration and tests

## Troubleshooting

### Enable Debug Logging

If you need more detailed output, add this to your test script or Django shell:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check SNMP Manually

Use system SNMP tools to verify device responds:

```bash
# Install net-snmp tools (if not already installed)
sudo apt-get install snmp snmp-mibs-downloader

# Test basic connectivity
snmpget -v2c -c public 10.10.10.6 1.3.6.1.2.1.1.5.0

# Walk interface table
snmpwalk -v2c -c public 10.10.10.6 1.3.6.1.2.1.2.2.1.2
```

If these commands don't work, the issue is with the device/network, not the Python code.

