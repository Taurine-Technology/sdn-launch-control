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

function EditBridgeDialogue({ open, handleClose, bridge, onBridgeUpdate }) {
    const [isLoading, setIsLoading] = useState(false);
    const [alert, setAlert] = useState({ show: false, type: '', message: '' });
    const [controllers, setControllers] = useState([]);
    const [selectedController, setSelectedController] = useState('');
    const [controllerPort, setControllerPort] = useState('');
    const [selectedPorts, setSelectedPorts] = useState([]);
    const [portOptions, setPortOptions] = useState([]);

    useEffect(() => {
        if (open) {
            fetchControllers();
            fetchPorts();
            if (bridge) {
                setSelectedController(bridge.controller ? bridge.controller.lan_ip_address : '');
                setControllerPort(bridge.controllerPort || '6653');
                setSelectedPorts(bridge.ports.map(port => port.name));
            }
        }
    }, [open, bridge]);

    const fetchControllers = async () => {
        setIsLoading(true);
        try {
            const response = await axios.get(`http://localhost:8000/controllers/`);
            setControllers(response.data || []);
        } catch (error) {
            console.error('Error fetching controllers:', error);
            setAlert({ show: true, type: 'error', message: 'Failed to fetch controllers' });
        } finally {
            setIsLoading(false);
        }
    };

    const fetchPorts = async () => {
        // Implement fetchPorts similar to fetchControllers
        // Assume the ports are fetched based on the device IP or some other relevant criteria
    };

    const handleControllerChange = (event) => {
        setSelectedController(event.target.value);
        // Optionally, set a default controller port if a controller is selected
        if (event.target.value) {
            setControllerPort('6653'); // Default port, adjust as necessary
        } else {
            setControllerPort('');
        }
    };

    const handlePortChange = (event) => {
        setSelectedPorts(event.target.value);
    };

    const handleSubmit = async () => {
        setIsLoading(true);
        // Prepare the payload with the bridge ID, selected controller, controller port, and selected ports
        // Adjust this according to how your backend expects to receive the updated bridge data

        try {
            const response = await axios.put(`http://localhost:8000/update-bridge/${bridge.id}/`, {
                // Payload data here
            });
            setAlert({ show: true, type: 'success', message: 'Bridge updated successfully' });
            onBridgeUpdate(); // Callback to refresh bridge list or data
        } catch (error) {
            console.error('Error updating bridge:', error);
            setAlert({ show: true, type: 'error', message: 'Failed to update bridge' });
        } finally {
            setIsLoading(false);
            handleClose(); // Close the dialog
        }
    };

    return (
        <Dialog open={open} onClose={handleClose} sx={{ '& .MuiDialog-paper': { minWidth: '500px' } }} >
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
                <Button onClick={handleClose} color="secondary">Cancel</Button>
                <Button onClick={handleSubmit} color="primary">Update</Button>
            </DialogActions>
        </Dialog>
    );
}

export default EditBridgeDialogue;
