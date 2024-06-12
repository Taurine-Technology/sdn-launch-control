import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, TextField, DialogActions, Button } from '@mui/material';
import axios from 'axios';

const CreateMeterDialog = ({ open, handleClose, controllerIP, deviceId }) => {
    const [rate, setRate] = useState('');

    const handleSubmit = async () => {
        try {
            const payload = {
                controller_ip: controllerIP,
                switch_id: deviceId,
                rate: rate
            };
            const response = await axios.post('http://localhost:8000/onos/create-meter/', payload);
            if (response.status === 201) {
                alert('Successfully created meter');
            } else {
                alert('Failed to create meter');
            }
        } catch (error) {
            alert('Error in creating meter: ' + error.message);
        }
        handleClose();
    };

    return (
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>Create New Meter</DialogTitle>
            <DialogContent>
                <TextField
                    autoFocus
                    margin="dense"
                    id="rate"
                    label="Rate (KB/s)"
                    type="number"
                    fullWidth
                    variant="standard"
                    value={rate}
                    onChange={(e) => setRate(e.target.value)}
                />
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose}>Cancel</Button>
                <Button onClick={handleSubmit}>Create</Button>
            </DialogActions>
        </Dialog>
    );
};

export default CreateMeterDialog;
