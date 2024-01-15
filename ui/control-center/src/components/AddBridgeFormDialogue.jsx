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
    Alert, Chip, OutlinedInput,
} from '@mui/material';
import axios from 'axios';

const AddBridgeFormDialogue = ({deviceIp} ) => {
    const [open, setOpen] = useState(false);
    const [bridgeName, setBridgeName] = useState('');
    const [openFlowVersion, setOpenFlowVersion] = useState('1.3');
    const [selectedPorts, setSelectedPorts] = useState([]);
    const [portOptions, setPortOptions] = useState(['none']);
    const [isLoading, setIsLoading] = useState(false);
    const [alert, setAlert] = useState({ show: false, type: '', message: '' });


    const handleClickOpen = () => setOpen(true);
    const handleClose = () => {
        setOpen(false);
        setBridgeName('');
        setOpenFlowVersion('1.3');
        setSelectedPorts([]);
        setPortOptions(['none'])
        setAlert({ show: false, type: '', message: '' })
    };
    useEffect(() => {
        if (open) {
            fetchPorts();
        }
    }, [open, deviceIp]);
    const fetchPorts = async () => {
        try {
            console.log(deviceIp)
            const response = await axios.get(`http://localhost:8000/get-device-ports/${deviceIp}/`);
            if (response.data.status === 'success') {
                setPortOptions(['none', ...response.data.interfaces]);
                console.log(response.data.interfaces)
            }
            // Handle other statuses if needed
        } catch (error) {
            console.error('Error fetching ports:', error);
            // Handle error
        }
    };
    const handleSubmit = async () => {
        setIsLoading(true);
        setAlert({ show: false, type: '', message: '' })
        const payload = {
            name: bridgeName,
            openFlowVersion: openFlowVersion,
            ports: selectedPorts,
        };

        try {
            const response = await axios.post('http://localhost:8000/add-bridge/', payload);
            setAlert({ show: true, type: 'success', message: 'Bridge added successfully' });
        } catch (error) {
            setAlert({ show: true, type: 'error', message: 'Error adding bridge' });
        } finally {
            setIsLoading(false);
        }
    };

    const handlePortChange = (event) => {
        setSelectedPorts(event.target.value);
    };

    return (
        <div>
            <Button variant="contained" onClick={handleClickOpen} sx={{marginTop: 4}}>
                Add Bridge
            </Button>
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Add Bridge</DialogTitle>
                <DialogContent>
                    {isLoading && <CircularProgress />}
                    {!isLoading && (
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
{alert.show && <Alert severity={alert.type}>{alert.message}</Alert>}
</Dialog>
        </div>
    );
};

export default AddBridgeFormDialogue;
