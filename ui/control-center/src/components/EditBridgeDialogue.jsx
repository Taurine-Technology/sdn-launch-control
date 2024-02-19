import React, { useEffect, useState } from 'react';
import {
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    CircularProgress,
    Chip,
    OutlinedInput,
    Box,
    Alert, TextField,
} from '@mui/material';
import axios from 'axios';

function EditBridgeDialogue({ open, handleClose, bridge, onBridgeUpdate, deviceIp }) {
    const [isLoading, setIsLoading] = useState(false);
    const [alert, setAlert] = useState({ show: false, type: '', message: '' });
    const [controllers, setControllers] = useState([]);
    const [selectedController, setSelectedController] = useState('');
    const [controllerPort, setControllerPort] = useState('');
    const [selectedPorts, setSelectedPorts] = useState([]);
    const [portOptions, setPortOptions] = useState([]);
    useEffect(() => {
        if (open) {
            fetchData();

            if (bridge && portOptions) {
                setSelectedController(bridge.controller ? bridge.controller.lan_ip_address : '');
                setControllerPort(bridge.controllerPort || '6653');
                setSelectedPorts(bridge.ports.map(port => port.name));
            }

        }
    }, [open, bridge, deviceIp]);
    const fetchData = async () => {
        setIsLoading(true);
        await fetchControllers();
        await fetchPorts();
        setIsLoading(false);
    }
    const fetchControllers = async () => {
        try {

            const response = await axios.get(`http://localhost:8000/controllers/`);

            setControllers(response.data || []);

        } catch (error) {
            console.error('Error fetching controllers:', error);
            setAlert({ show: true, type: 'error', message: 'Failed to fetch controllers' });
        }
    };

    const fetchPorts = async () => {
        try {
            console.log(deviceIp)
            const response = await axios.get(`http://localhost:8000/get-device-ports/${deviceIp}/`);
            if (response.data.status === 'success') {
                if (response.data.interfaces == null) {
                    setPortOptions(['none']);
                    console.log('here')
                    setIsLoading(false)
                } else {
                    setPortOptions(response.data.interfaces);
                }
                console.log(response.data.interfaces)
            }
        } catch (error) {
            console.error('Error fetching ports:', error);

        }
    };

    const handleControllerChange = (event) => {
        setSelectedController(event.target.value);
        if (event.target.value) {
            setControllerPort('6653');
        } else {
            setControllerPort('');
        }
    };

    const handlePortChange = (event) => {
        setSelectedPorts(event.target.value);
    };

    const handleSubmit = async () => {
        setAlert('')
        setAlert({ show: false, type: '', message: '' });
        setIsLoading(true);
        const payload = {
            lan_ip_address: deviceIp,
            name: bridge.name,
            controller: selectedController ? controllers.find(c => c.lan_ip_address === selectedController) : null,
            port: controllerPort,
            ports: selectedPorts,
        }
        try {
            const response = await axios.put(`http://localhost:8000/update-bridge/`, payload);
            if (response.data.status === 'success') {
                setAlert({ show: true, type: 'success', message: 'Bridge updated successfully' });
                onBridgeUpdate();
            }
            else {
                setAlert({ show: true, type: 'error', message: 'Failed to update bridge' });
            }
        } catch (error) {
            console.error('Error updating bridge:', error);
            setAlert({ show: true, type: 'error', message: 'Failed to update bridge' });
        } finally {
            setIsLoading(false);

        }
    };

    return (
        <Dialog open={open} onClose={handleClose} sx={{ '& .MuiDialog-paper': { minWidth: '600px' } }} >
            <DialogTitle>Edit Bridge</DialogTitle>
            <DialogContent>
                {alert.show && <Alert severity={alert.type} onClose={() => setAlert({ show: false })}>{alert.message}</Alert>}
                {isLoading ? (
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                        <CircularProgress />
                    </Box>
                ) : (
                    <div>
                        <FormControl fullWidth margin="dense">
                            <InputLabel>Controller</InputLabel>
                            <Select
                                value={selectedController}
                                onChange={handleControllerChange}
                                label="Controller"
                            >
                                <MenuItem value="">None</MenuItem>
                                {controllers.map(controller => (
                                    <MenuItem key={controller.id} value={controller.lan_ip_address}>{controller.lan_ip_address}</MenuItem>
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
                                disabled={true}
                            />
                        )}
                        <FormControl fullWidth margin="dense">
                            <InputLabel>Ports</InputLabel>
                            <Select
                                multiple
                                value={selectedPorts}
                                onChange={handlePortChange}
                                input={<OutlinedInput label="Ports" />}
                                renderValue={selected => (
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {selected.map(value => (
                                            <Chip key={value} label={value} />
                                        ))}
                                    </Box>
                                )}
                            >
                                {portOptions.map(port => (
                                    <MenuItem key={port} value={port}>
                                        {port}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </div>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} color="button_green">Cancel</Button>
                <Button onClick={handleSubmit} color="button_red">Update</Button>
            </DialogActions>
        </Dialog>
    );
}

export default EditBridgeDialogue;
