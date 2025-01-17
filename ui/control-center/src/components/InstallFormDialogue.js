/**
 * File: InstallFormDialogue.js
 * Copyright (C) 2025 Keegan White
 *
 * This file is part of the SDN Launch Control project.
 *
 * This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
 * available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
 *
 * Contributions to this project are governed by a Contributor License Agreement (CLA).
 * By submitting a contribution, contributors grant Keegan White exclusive rights to
 * the contribution, including the right to relicense it under a different license
 * at the copyright owner's discretion.
 *
 * Unless required by applicable law or agreed to in writing, software distributed
 * under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the GNU General Public License for more details.
 *
 * For inquiries, contact Keegan White at keeganwhite@taurinetech.com.
 */

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
    InputLabel, FormControl, Alert, IconButton
} from '@mui/material';
import axios from 'axios';
import DownloadIcon from "@mui/icons-material/Download";
// Set the base URL for axios
// axios.defaults.baseURL = 'http://localhost';
const InstallFormDialogue = ({ installationType, endpoint }) => {
    const [open, setOpen] = useState(false);
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState('');
    const [fetchingDevices, setFetchingDevices] = useState(false);
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
    const [apiUrl, setApiUrl] = useState('')

    useEffect(() => {
        fetchDevices();
    }, []);

    const fetchDevices = async () => {
        setFetchingDevices(true);
        try {
            const response = await axios.get('http://localhost:8000/devices/'); // Adjust the URL as needed
            setDevices(response.data);
        } catch (error) {
            console.error('Failed to fetch devices', error);
        } finally {
            setFetchingDevices(false);
        }
    };

    useEffect(() => {
        updateFormValidity();
    }, [name, host, username, password, apiUrl]);
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
        const isValid = (name && host && username && password && apiUrl);
        setIsFormValid(isValid);
    };

    const handleSelectDevice = (event) => {
        const deviceID = event.target.value;
        if (deviceID === "" || deviceID === "none") { // Check if "None" option is selected
            // Reset form fields for manual input
            setSelectedDevice('');
            setDeviceName('');
            setHost('');
            setDeviceType('switch'); // Reset to default or keep empty
            setUsername('');
            setPassword('');
            setOs('ubuntu_20_server'); // Reset to default or keep empty
        } else {
            const device = devices.find(d => d.lan_ip_address === deviceID);
            if (device) {
                setSelectedDevice(deviceID);
                setDeviceName(device.name);
                setHost(device.lan_ip_address);
                setDeviceType(device.device_type);
                setUsername(device.username);
                setPassword(device.password);
                setOs(device.os_type);
            }
        }
        updateFormValidity();
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
    const handleApiUrlChange = (e) => {
        setApiUrl(e.target.value)
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
        formData.append('api_url', apiUrl)
        const addDevicePayload = {
            name: name,
            device_type: deviceType,
            os_type: operating_system,
            lan_ip_address: host,
        };
        try {
            const deployResponse = await axios.post(`http://localhost:8000/${endpoint}/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            // const addDeviceResponse = await axios.post('http://localhost:8000/add-device/', addDevicePayload);
            console.log('Deploy Response:', deployResponse.data.message);

            // console.log('Add Device Response:', addDeviceResponse.data.message);
            // || addDeviceResponse.data.message
            setResponseMessage(deployResponse.data.message);
            setResponseType('success');
            if (endpoint === 'install-ovs') {
                const monitorPayload = {
                    lan_ip_address: formData.get('lan_ip_address'),
                    username: formData.get('username'),
                    password: formData.get('password'),
                    api_url: formData.get('api_url')
                };

                const installSystemResponse = await axios.post('http://localhost:8000/install_system_stats_monitor/', monitorPayload, {
                    headers: {'Content-Type': 'application/json'}
                });
                console.log('installSystemResponse Response:', installSystemResponse.data.message);
            }
        } catch (error) {
            console.error('Error:', error || 'Deployment failed');
            setResponseMessage(error.response?.data?.message || error.message || 'Deployment failed');
            setResponseType('error');
        } finally {
            setIsLoading(false);
            setFile(null);
            // handleClose();
        }

        // handleClose();
    };

    return (
        <div>
            <div>

                <IconButton color="primary" onClick={handleClickOpen}>
                    <DownloadIcon />
                </IconButton>
                <Dialog open={open} onClose={handleOnClose}>
                    <DialogTitle>{`Install ${installationType}`}</DialogTitle>
                    { (isLoading || fetchingDevices) && (
                        <CircularProgress style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex:1000 }} />
                    )}
                    {responseMessage && (
                        <Alert severity={responseType} onClose={handleCloseAlert}>
                            {responseMessage}
                        </Alert>
                    )}

                    <DialogContent>
                        <FormControl fullWidth margin="dense">
                            <InputLabel id="device-select-label">Select Device</InputLabel>
                            <Select
                                labelId="device-select-label"
                                value={selectedDevice}
                                onChange={handleSelectDevice}
                                label="Select Device"
                                disabled={isLoading}
                            >
                                <MenuItem value="">Manual Device Entry</MenuItem>
                                {devices.map((device) => (
                                    <MenuItem key={device.lan_ip_address} value={device.lan_ip_address}>
                                        {device.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>

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
                        <TextField
                            margin="dense"
                            label="API URL"
                            fullWidth
                            variant="outlined"
                            value={apiUrl}
                            onChange={handleApiUrlChange}
                            required
                            disabled={isLoading}
                        />
                    </DialogContent>
                    <DialogActions>
                        <Button
                            disabled={isLoading}
                            variant="contained"
                            onClick={handleClose}
                            sx = {{ bgcolor: '#02032F'}}
                        >
                            Cancel
                        </Button>
                        <Button
                            disabled={isLoading || !isFormValid}
                            variant="contained"
                            onClick={handleSubmit}
                            sx = {{ bgcolor: '#02032F'}}
                        >
                            Install
                        </Button>
                    </DialogActions>
                </Dialog>
            </div>
        </div>
    );
};

export default InstallFormDialogue;
