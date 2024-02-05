import React, {useEffect, useState} from 'react';
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    CircularProgress,
    Alert,
    Fab, Box
} from '@mui/material';
import axios from 'axios';
import AddIcon from '@mui/icons-material/Add';
const AddDeviceDialogue = ({fetchDevices}) => {
    const [open, setOpen] = useState(false);
    const [device, setDevice] = useState({
        name: '',
        device_type: 'switch',
        os_type: 'ubuntu_20_server',
        username: '',
        password: '',
        lan_ip_address: ''
    });
    const [operating_system, setOs] = useState('ubuntu_20_server');
    const [ovs, setOvs] = useState(false);
    const [ovsVersion, setOvsVersion] = useState('');
    const [openFlowVersion, setOpenFlowVersion] = useState('');
    const [host, setHost] = useState('');
    const [numPorts, setNumPorts] = useState(0);
    const [name, setDeviceName] = useState('');
    const [deviceType, setDeviceType] = useState('switch');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState('');
    const [isFormValid, setIsFormValid] = useState(false);
    useEffect(() => {
        updateFormValidity();
    }, [name, host, username, password, deviceType, ovs, operating_system, numPorts, ovs, ovsVersion, openFlowVersion]);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);
    const updateFormValidity = () => {
        const isValid = name && host && username && password && operating_system;
        setIsFormValid(isValid);
    };
    const handleChange = (e) => {
        const { name, value } = e.target;
        setDevice(prev => ({ ...prev, [name]: value }));
        updateFormValidity();
    };

    const handleSubmit = async () => {
        setIsLoading(true);
        try {
            const formData = new FormData();
            formData.append('name', name);
            formData.append('device_type', deviceType);
            formData.append('lan_ip_address', host);
            formData.append('username', username);
            formData.append('password', password);
            formData.append('os_type', operating_system);
            formData.append('ports', numPorts);
            formData.append('ovs_enabled', ovs);
            formData.append('ovs_version', ovsVersion);
            formData.append('openflow_version', openFlowVersion);

            const response = await axios.post('http://localhost:8000/add-device/', formData,
            {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResponseMessage(response.data.message);
            setResponseType('success');
            setOs('ubuntu_20_server');
            setOvs(false);
            setOvsVersion('');
            setOpenFlowVersion('');
            setHost('');
            setNumPorts(0);
            setDeviceType('switch')
            setUsername('');
            setPassword('');
            // Refresh or update device list in parent component if needed
        } catch (error) {
            setResponseType('error');
            setResponseMessage(error.response?.data?.message || error.message || 'Failed to add device');
        } finally {
            setIsLoading(false);
            fetchDevices();
        }
    };
    const handleOSChange = (e) => {
        setOs(e.target.value)
        updateFormValidity();
    };
    const handleOvsChange = (e) => {
        const isOvsEnabled = e.target.value === 'True';
        setOvs(isOvsEnabled);
        // Automatically set and disable ovsVersion and openFlowVersion if OVS is disabled
        if (!isOvsEnabled) {
            setOvsVersion('None');
            setOpenFlowVersion('None');
        } else {
            // Reset to default or empty values if OVS is enabled
            setOvsVersion('');
            setOpenFlowVersion('');
        }
        updateFormValidity();
    };

    const handleOvsVersionChange = (e) => {
        setOvsVersion(e.target.value)
        updateFormValidity();
    };
    const handleOpenFlowVersionVersionChange = (e) => {
        setOpenFlowVersion(e.target.value)
        updateFormValidity();
    };
    const handleTypeChange = (e) => {
        setDeviceType(e.target.value)
        updateFormValidity();
    };
    const handleOnClose = (event, reason) => {
        if (isLoading && reason && reason === "backdropClick") {
            // Prevent closing the dialog
            return;
        } else if (isLoading && reason && reason === "escapeKeyDown") {
            // Prevent closing the dialog on escape key press
            return;
        }
        // Call handleClose if provided
        if (typeof handleClose === 'function') {
            handleClose();
        }

    };

    return (
        <div>

            <Fab
                color="button_green"
                aria-label="add"
                style={{ position: 'fixed', right: 30, bottom: 100 }}
                onClick={handleOpen}
            >
                <AddIcon />
            </Fab>
            <Dialog open={open} onClose={handleOnClose}>
                <DialogTitle>Add New Device</DialogTitle>
                {isLoading ? (
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                        <CircularProgress />
                    </Box>
                ) : (
                <DialogContent>
                    {responseMessage && (
                        <Alert severity={responseType} onClose={() => setResponseMessage('')}>
                            {responseMessage}
                        </Alert>
                    )}
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Device Name"
                        fullWidth
                        variant="outlined"
                        value={name}
                        onChange={e => {
                            setDeviceName(e.target.value)
                            updateFormValidity();
                        }}
                        required
                        disabled={isLoading}
                    />
                    <TextField
                        margin="dense"
                        label="LAN IP Address"
                        fullWidth
                        variant="outlined"
                        value={host}
                        onChange={e => {
                            setHost(e.target.value)
                            updateFormValidity();
                        }}
                        required
                        disabled={isLoading}
                    />
                    <TextField
                        margin="dense"
                        label="Username"
                        fullWidth
                        variant="outlined"
                        value={username}
                        onChange={e => {
                            setUsername(e.target.value)
                            updateFormValidity();
                        }}
                        required
                        disabled={isLoading}
                    />
                    <TextField
                        margin="dense"
                        label="Password"
                        fullWidth variant="outlined"
                        type="password"
                        value={password}
                        onChange={
                            e => {
                                setPassword(e.target.value)
                                updateFormValidity();
                            }
                        }
                        required
                        disabled={isLoading}
                    />

                    <TextField
                        margin="dense"
                        label="Number of Ports"
                        fullWidth variant="outlined"
                        type="number"
                        value={numPorts}
                        onChange={
                            e => {
                                setNumPorts(e.target.value)
                                updateFormValidity();
                            }
                        }
                        required
                        disabled={isLoading}
                    />

                    <FormControl fullWidth margin="dense" disabled={isLoading}>
                        <InputLabel id="os-select-label">Operating System</InputLabel>
                        <Select
                            labelId="os-select-label"
                            value={operating_system}
                            onChange={handleOSChange}
                            label="Operating System"
                        >
                            <MenuItem value={'ubuntu_20_server'}>Ubuntu 20.04 Server</MenuItem>
                            <MenuItem value={'other'}>Other</MenuItem>
                        </Select>
                    </FormControl>
                    <FormControl fullWidth margin="normal" disabled={isLoading}>
                        <InputLabel>Device Type</InputLabel>
                        <Select
                            name="device_type"
                            value={deviceType}
                            label="Device Type"
                            onChange={handleTypeChange}
                        >
                            <MenuItem value="switch">Switch</MenuItem>
                            <MenuItem value="access_point">Access Point</MenuItem>
                            <MenuItem value="server">Server</MenuItem>
                        </Select>
                    </FormControl>
                    <FormControl fullWidth margin="dense" disabled={isLoading}>
                        <InputLabel id="ovs-select-label">OVS Enabled</InputLabel>
                        <Select
                            labelId="ovs-select-label"
                            value={ovs ? 'True' : 'False'}
                            onChange={handleOvsChange}
                            label="OVS Enabled"
                        >
                            <MenuItem value={'False'}>False</MenuItem>
                            <MenuItem value={'True'}>True</MenuItem>
                        </Select>
                    </FormControl>

                    <FormControl fullWidth margin="dense" disabled={!ovs || isLoading}>
                        <InputLabel id="ovs-version-select-label">OVS Version</InputLabel>
                        <Select
                            labelId="ovs-version-select-label"
                            value={ovsVersion}
                            onChange={handleOvsVersionChange}
                            label="OVS Version"
                        >
                            <MenuItem value={'None'}>None</MenuItem>
                            <MenuItem value={'2.17.7'}>2.17.7</MenuItem>
                            <MenuItem value={'Other'}>Other</MenuItem>
                        </Select>
                    </FormControl>

                    <FormControl fullWidth margin="dense" disabled={isLoading}>
                        <InputLabel id="openflow-version-select-label">OpenFlow Version</InputLabel>
                        <Select
                            labelId="openflow-version-select-label"
                            value={openFlowVersion}
                            onChange={handleOpenFlowVersionVersionChange}
                            label="OpenFlow Version"
                        >
                            <MenuItem value={'None'}>None</MenuItem>
                            <MenuItem value={'1.0'}>1.0</MenuItem>
                            <MenuItem value={'1.3'}>1.3</MenuItem>
                            <MenuItem value={'Other'}>Other</MenuItem>
                        </Select>
                    </FormControl>

                </DialogContent>
                )}
                <DialogActions>
                    <Button color='button_red' onClick={handleClose}>Cancel</Button>
                    <Button color='button_green' onClick={handleSubmit} disabled={isLoading || !isFormValid}>Add</Button>
                </DialogActions>
            </Dialog>
        </div>
    );
};

export default AddDeviceDialogue;
