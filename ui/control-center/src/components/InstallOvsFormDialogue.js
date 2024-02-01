import React, {useEffect, useState} from 'react';
import {
    Button,
    TextField,
    Dialog,
    CircularProgress,
    DialogActions,
    DialogContent,
    DialogTitle,
    Select,
    MenuItem,
    InputLabel, FormControl, Alert
} from '@mui/material';
import axios from 'axios';
// Set the base URL for axios
// axios.defaults.baseURL = 'http://localhost';
const InstallOvsFormDialogue = () => {
    const [open, setOpen] = useState(false);
    const [host, setHost] = useState('');
    const [name, setDeviceName] = useState('');
    const [deviceType, setDeviceType] = useState('switch');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [file, setFile] = useState(null);
    const [operating_system, setOs] = useState('ubuntu_20_server');
    const [tempDir, setTempDir] = useState('/tmp');
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState(''); // 'success' or 'error'
    const [isLoading, setIsLoading] = useState(false);
    const [isFormValid, setIsFormValid] = useState(false);

    useEffect(() => {
        updateFormValidity();
    }, [name, host, username, password, file]);
    useEffect(() => {
        if (window && window.process && window.process.type) {
            const { ipcRenderer } = window.require('electron');
            ipcRenderer.on('set-temp-path', (event, path) => {
                setTempDir(path);
            });
        }
    }, []);
    useEffect(() => {
        console.log('isLoading state updated:', isLoading);
    }, [isLoading]);
    const updateFormValidity = () => {
        const isValid = name && host && username && password;
        setIsFormValid(isValid);
    };

    const handleCloseAlert = () => {
        setResponseMessage('');
    };
    const handleClickOpen = () => setOpen(true);
    const handleClose = () => {
        setOpen(false)
        setFile(null);
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
    const handleOSChange = (e) => {
        setOs(e.target.value)
        updateFormValidity();
    };
    const handleTypeChange = (e) => {
        setDeviceType(e.target.value)
        updateFormValidity();
    };
    const handleSubmit = async () => {
        console.log('Before setLoading:', isLoading);
        setIsLoading(true);
        console.log('After setLoading:', isLoading);

        const formData = new FormData();
        formData.append('name', name);
        formData.append('device_type', deviceType);
        formData.append('lan_ip_address', host);
        formData.append('username', username);
        formData.append('password', password);
        formData.append('os_type', operating_system);
        const addDevicePayload = {
            name: name,
            device_type: deviceType,
            os_type: operating_system,
            lan_ip_address: host,
        };
        try {
            const deployResponse = await axios.post('http://localhost:8000/install-ovs/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            // const addDeviceResponse = await axios.post('http://localhost:8000/add-device/', addDevicePayload);
            console.log('Deploy Response:', deployResponse.data.message);
            // console.log('Add Device Response:', addDeviceResponse.data.message);
            // || addDeviceResponse.data.message
            setResponseMessage(deployResponse.data.message);
            setResponseType('success');
        } catch (error) {
            console.error('Error:', error || 'Deployment failed');
            setResponseMessage(error.response?.data?.message || error.message || 'Deployment failed');
            setResponseType('error');
        } finally {
            setIsLoading(false);
            setFile(null);
            handleClose();
        }

        handleClose();
    };

    return (
        <div>

            <div>
                {responseMessage && (
                    <Alert severity={responseType} onClose={handleCloseAlert}>
                        {responseMessage}
                    </Alert>
                )}
                <Button variant="contained" onClick={handleClickOpen}>
                    Install Open vSwitch
                </Button>
                <Dialog open={open} onClose={handleOnClose}>
                    <DialogTitle>Install OVS</DialogTitle>
                    {isLoading && (
                        <CircularProgress style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex:1000}} />
                    )}
                    <DialogContent>
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
                        <FormControl fullWidth margin="dense" disabled={isLoading}>
                            <InputLabel id="os-select-label">Operating System</InputLabel>
                            <Select
                                labelId="os-select-label"
                                value={operating_system}
                                onChange={handleOSChange}
                                label="Operating System"
                            >
                                <MenuItem value={'ubuntu_20_server'}>Ubuntu 20.04 Server</MenuItem>
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
                    </DialogContent>
                    <DialogActions>
                        <Button
                            disabled={isLoading}
                            variant="contained"
                            onClick={handleClose}
                        >
                            Cancel
                        </Button>
                        <Button
                            disabled={isLoading || !isFormValid}
                            variant="contained"
                            onClick={handleSubmit}
                        >
                            Install
                        </Button>
                    </DialogActions>
                </Dialog>
            </div>

        </div>
    );
};

export default InstallOvsFormDialogue;
