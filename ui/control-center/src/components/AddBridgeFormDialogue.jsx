/**
 * File: AddBridgeFormDialogue.jsx
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
import React, { useEffect, useState } from 'react';
import {
    Button,
    TextField,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Select,
    MenuItem,
    InputLabel,
    FormControl,
    CircularProgress,
    Alert, Chip, OutlinedInput, Box,
} from '@mui/material';
import axios from 'axios';

const AddBridgeFormDialogue = ({ deviceIp, onDialogueClose }) => {
    const [open, setOpen] = useState(false);
    const [bridgeName, setBridgeName] = useState('');
    const [openFlowVersion, setOpenFlowVersion] = useState('1.3');
    const [selectedPorts, setSelectedPorts] = useState([]);
    const [portOptions, setPortOptions] = useState(['none']);
    const [isLoading, setIsLoading] = useState(false);
    const [alert, setAlert] = useState({ show: false, type: '', message: '' });
    const [controllers, setControllers] = useState([]);
    const [selectedController, setSelectedController] = useState('');
    const [controllerPort, setControllerPort] = useState('6653');
    const [apiUrl, setApiUrl] = useState('')



    const handleCloseAlert = () => {
        setAlert({show: false, type: '', message: ''});
    };
    const handleClickOpen = () => setOpen(true);
    const handleClose = () => {
        setOpen(false);
        setBridgeName('');
        setOpenFlowVersion('1.3');
        setSelectedPorts([]);
        setPortOptions(['none'])
        setAlert({ show: false, type: '', message: '' })
        if (onDialogueClose) {
            onDialogueClose(); // Call the callback function to refresh bridges
        }
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
    useEffect(() => {
        if (open) {

            fetchPorts();
            fetchControllers();

        }
    }, [open, deviceIp]);
    const fetchPorts = async () => {
        try {
            setIsLoading(true)
            console.log(deviceIp)
            const response = await axios.get(`http://localhost:8000/unassigned-device-ports/${deviceIp}/`);
            if (response.data.status === 'success') {
                if (response.data.interfaces == null) {
                    setPortOptions(['none']);
                    console.log('here')
                    setIsLoading(false)
                } else {
                    setPortOptions(response.data.interfaces);
                    setIsLoading(false)
                }

                console.log(response.data.interfaces)
            }
            // Handle other statuses if needed
        } catch (error) {
            console.error('Error fetching ports:', error);
            // Handle error
        }
    };

    const fetchControllers = async () => {
        try {
            const response = await axios.get(`http://localhost:8000/controllers/`);
            console.log(response.data)
            setControllers(response.data);
        } catch (error) {
            console.error('Error fetching controllers:', error);
            console.log('could not fetch controllers')
        }
    };
    const handleSubmit = async () => {
        setIsLoading(true);
        setAlert({ show: false, type: '', message: '' })
        let payload = {
            lan_ip_address: deviceIp,
            name: bridgeName,
            openFlowVersion: openFlowVersion,
            ports: selectedPorts,
            api_url: apiUrl,
        };

        if (selectedController) {
            payload = {
                ...payload,
                controller_ip: selectedController,
                controller_port: controllerPort,
            };
        }

        try {
            console.log(payload)
            const response = await axios.post('http://localhost:8000/add-bridge/', payload);

            const qosMonitorResponse = await axios.post('http://localhost:8000/install-ovs-qos-monitor/', payload);
            setAlert({ show: true, type: 'success', message: 'Bridge added successfully' });
            if (onDialogueClose) {
                onDialogueClose(); // Call the callback function to refresh bridges
            }
        } catch (error) {
            console.log('Error Response:', error.response);
            setAlert({ show: true, type: 'error', message: error.response?.data?.message || error.message || 'Error adding bridge' });
        } finally {
            fetchPorts();
            setBridgeName('');
            setOpenFlowVersion('1.3');
            setSelectedPorts([]);
            setIsLoading(false);
            setSelectedController('')
            // setOpen(false);

        }
    };

    const handlePortChange = (event) => {
        console.log(event.target.value)
        setSelectedPorts(event.target.value);
    };

    return (
        <div>
            <Button variant="contained" onClick={handleClickOpen} sx={{marginTop: 4}}>
                Add Bridge
            </Button>
            <Dialog open={open} onClose={handleOnClose} sx={{ '& .MuiDialog-paper': { minWidth: '600px' } }} >
                <DialogTitle>Add Bridge</DialogTitle>
                <DialogContent>
                    {alert.show && <Alert severity={alert.type} onClose={handleCloseAlert}>{alert.message}</Alert>}
                    {isLoading ? (
                        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                            <CircularProgress />
                        </Box>
                    ) : (
                        <div>
                            <TextField
                                autoFocus
                                margin="dense"
                                label="Bridge Name"
                                fullWidth
                                variant="outlined"
                                value={bridgeName}
                                onChange={e => setBridgeName(e.target.value)}
                                required
                            />
                            <TextField
                                autoFocus
                                margin="dense"
                                label="API URL"
                                fullWidth
                                variant="outlined"
                                value={apiUrl}
                                onChange={e => setApiUrl(e.target.value)}
                                required
                            />
                            <FormControl fullWidth margin="dense">
                                <InputLabel>OpenFlow Version</InputLabel>
                                <Select
                                    value={openFlowVersion}
                                    onChange={e => setOpenFlowVersion(e.target.value)}
                                    label="OpenFlow Version"
                                >
                                    <MenuItem value="1.3">1.3</MenuItem>
                                </Select>
                            </FormControl>
                            <FormControl fullWidth margin="dense">
                                <InputLabel>Ports</InputLabel>
                                <Select
                                    multiple
                                    value={selectedPorts}
                                    onChange={handlePortChange}
                                    input={<OutlinedInput label="Ports" />}
                                    renderValue={(selected) => (
                                        <div>
                                            {selected.map((value) => (
                                                <Chip key={value} label={value} />
                                            ))}
                                        </div>
                                    )}
                                >
                                    {portOptions.map((port) => (
                                        <MenuItem key={port} value={port}>
                                            {port}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <FormControl fullWidth margin="dense">
                                <InputLabel>Controller</InputLabel>
                                <Select
                                    value={selectedController}
                                    onChange={e => {
                                        setSelectedController(e.target.value);
                                        // Set default port if a controller is selected, otherwise empty
                                        setControllerPort(e.target.value ? '6653' : '');
                                    }}
                                    label="Controller"
                                >
                                    <MenuItem value="">None</MenuItem>
                                    {controllers.map((controller) => (
                                        <MenuItem key={controller.id} value={controller.lan_ip_address}>
                                            {controller.lan_ip_address}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            {selectedController && (
                                <TextField
                                    margin="dense"
                                    label="Controller Port"
                                    fullWidth
                                    variant="outlined"
                                    value={controllerPort}
                                    onChange={e => setControllerPort(e.target.value)}
                                    required
                                />
                            )}
                        </div>
                    )}
                </DialogContent>

                <DialogActions>
            <Button onClick={handleClose} color="button_red" disabled={isLoading}>
                Cancel
            </Button>
            <Button color="button_green" onClick={handleSubmit} disabled={isLoading || !bridgeName || selectedPorts.length === 0}>
                Submit
            </Button>
        </DialogActions>

</Dialog>
        </div>
    );
};

export default AddBridgeFormDialogue;
