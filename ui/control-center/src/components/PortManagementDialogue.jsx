import React, { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, Button, FormControl, Select, MenuItem, List, ListItem, ListItemText } from '@mui/material';
import axios from "axios";

function PortManagementDialogue({ open, handleClose, device }) {
    // State for managing ports and bridges
    const [ports, setPorts] = useState([]);
    const [bridges, setBridges] = useState([]);
    const [selectedBridge, setSelectedBridge] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        // Fetch available bridges and ports from the backend
        const fetchBridges = async () => {
            try {
                const response = await axios.get('http://localhost:8000/devices/');
                setBridges(response.data); // Axios automatically handles JSON parsing
                console.log(response.data)
            } catch (error) {
                console.error('Error fetching devices:', error);
                setError(error.message);
            }
        };

        fetchBridges();

    }, [device]);

    // Handlers for bridge selection and port assignment
    const handleBridgeChange = (event) => {
        setSelectedBridge(event.target.value);
    };

    const handleAssignPort = (port) => {
        // Logic to assign port to selected bridge
    };

    return (
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>Manage Ports for {device.name}</DialogTitle>
            <DialogContent>
                <FormControl fullWidth>
                    <Select
                        value={selectedBridge}
                        onChange={handleBridgeChange}
                        displayEmpty
                        inputProps={{ 'aria-label': 'Without label' }}
                    >
                        {bridges.map(bridge => (
                            <MenuItem key={bridge.id} value={bridge.name}>{bridge.name}</MenuItem>
                        ))}
                    </Select>
                </FormControl>
                <List>
                    {ports.map(port => (
                        <ListItem
                            key={port.id}
                            button
                            onClick={() => handleAssignPort(port)}
                            disabled={port.assignedBridge === selectedBridge}
                        >
                            <ListItemText primary={port.name} />
                        </ListItem>
                    ))}
                </List>
            </DialogContent>
            <Button onClick={handleClose}>Close</Button>
        </Dialog>
    );
}

export default PortManagementDialogue;
