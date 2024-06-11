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

const InstallSnifferForm = () => {
    const [open, setOpen] = useState(false);
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState('');
    const [fetchingDevices, setFetchingDevices] = useState(false);
    const [host, setHost] = useState('');

    const [monitoringInterface, setMonitoringInterface] = useState('');
    const [clientPort, setClientPort] = useState('');
    const [wanPort, setWanPort] = useState('');

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
    }, [host, apiUrl, monitoringInterface, clientPort, wanPort]);

    useEffect(() => {
        console.log('isLoading state updated:', isLoading);
    }, [isLoading]);
    const updateFormValidity = () => {
        const isValid = (host && apiUrl && monitoringInterface && clientPort && wanPort);
        setIsFormValid(isValid);
    };

    const handleSelectDevice = (event) => {
        const deviceID = event.target.value;
        if (deviceID === "" || deviceID === "none") { // Check if "None" option is selected
            // Reset form fields for manual input
            setSelectedDevice('');
            setHost('');
        } else {
            const device = devices.find(d => d.lan_ip_address === deviceID);
            if (device) {
                setSelectedDevice(deviceID);
                setHost(device.lan_ip_address);
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

    const handleApiUrlChange = (e) => {
        setApiUrl(e.target.value)
        updateFormValidity();
    };

    const handleMonitoringInterfaceChange = (e) => {
        setMonitoringInterface(e.target.value)
        updateFormValidity();
    };

    const handleClientPortChange = (e) => {
        setClientPort(e.target.value)
        updateFormValidity();
    };

    const handleWanPortChange = (e) => {
        setWanPort(e.target.value)
        updateFormValidity();
    };

    const handleSubmit = async () => {
        console.log('Before setLoading:', isLoading);
        setIsLoading(true);
        console.log('After setLoading:', isLoading);

        const formData = new FormData();
        formData.append('lan_ip_address', host);
        formData.append('api_base_url', apiUrl)
        formData.append('monitor_interface', monitoringInterface)
        formData.append('port_to_client', clientPort)
        formData.append('port_to_router', wanPort)

        try {
            const deployResponse = await axios.post(`http://localhost:8000/install-sniffer/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            // const addDeviceResponse = await axios.post('http://localhost:8000/add-device/', addDevicePayload);
            console.log('Deploy Response:', deployResponse.data.message);

            // console.log('Add Device Response:', addDeviceResponse.data.message);
            // || addDeviceResponse.data.message
            setResponseMessage(deployResponse.data.message);
            setResponseType('success');
            if (deployResponse.data.status === 'success') {
                const payload = {
                    name: 'tau-traffic-classification-sniffer',
                    installed: true,
                    lan_ip_address: host
                };
                try {
                    const response = await axios.post('http://localhost:8000/install-plugin/', payload);
                    console.log('Response:', response.data);
                    setResponseMessage('Plugin installation status updated successfully!');
                    setResponseType('success');
                } catch (error) {
                    console.error('Installation error:', error);
                    setResponseMessage(error.response?.data?.message || 'Installed Sniffer but failed to update plugin status');
                    setResponseType('error');
                } finally {
                    setIsLoading(false);
                }
            }


        } catch (error) {
            console.error('Error:', error || 'Deployment failed');
            setResponseMessage(error.response?.data?.message || error.message || 'Deployment failed');
            setResponseType('error');
        } finally {
            setIsLoading(false);
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
                    <DialogTitle>{`Install Sniffer`}</DialogTitle>
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
                            margin="dense"
                            label="API URL"
                            fullWidth
                            variant="outlined"
                            value={apiUrl}
                            onChange={handleApiUrlChange}
                            required
                            disabled={isLoading}
                        />
                        <TextField
                            margin="dense"
                            label="Monitoring Interface Name"
                            fullWidth
                            variant="outlined"
                            value={monitoringInterface}
                            onChange={handleMonitoringInterfaceChange}
                            required
                            disabled={isLoading}
                        />
                        <TextField
                            margin="dense"
                            label="Client Port Number"
                            fullWidth
                            variant="outlined"
                            value={clientPort}
                            onChange={handleClientPortChange}
                            required
                            disabled={isLoading}
                        />
                        <TextField
                            margin="dense"
                            label="WAN Port Number"
                            fullWidth
                            variant="outlined"
                            value={wanPort}
                            onChange={handleWanPortChange}
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

export default InstallSnifferForm;

//http://10.10.10.2:8000
//eth2
//2
//1