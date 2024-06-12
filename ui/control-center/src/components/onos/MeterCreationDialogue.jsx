import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    TextField,
    DialogActions,
    Button,
    FormControl,
    InputLabel, Select, OutlinedInput, Chip, MenuItem
} from '@mui/material';
import axios from 'axios';
import Alert from "@mui/material/Alert";

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
    PaperProps: {
        style: {
            maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
            width: 250,
        },
    },
};

const CreateMeterDialog = ({ open, handleClose, controllerIP, deviceId, categories }) => {
    const [rate, setRate] = useState('');
    const [selectedCategories, setSelectedCategories] = useState([]);
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState(''); // 'success' or 'error'

    const handleChangeCategories = (event) => {
        setSelectedCategories(event.target.value);
    };
    const handleSubmit = async () => {
        try {
            const payload = {
                controller_ip: controllerIP,
                switch_id: deviceId,
                rate: rate,
                categories: categories
            };
            const response = await axios.post('http://localhost:8000/onos/create-meter/', payload);
            if (response.status === 201) {
                setResponseMessage('Successfully created meter');
                setResponseType('success')
            } else {
                setResponseMessage('Failed to create meter');
                setResponseType('error')
            }
        } catch (error) {
            console.log(error)
            setResponseMessage(error.message);
            setResponseType('error')
            if (error.message === "Request failed with status code 400") {
                setResponseMessage('This meter already exists. Assign categories to it directly.');
                setResponseType('error')
            }
        }
    };
    const handleCloseAlert = () => {
        setResponseMessage('')
    }

    return (
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>Create New Meter</DialogTitle>
            {responseMessage && (
                <Alert severity={responseType} onClose={handleCloseAlert}>
                    {responseMessage}
                </Alert>
            )}
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
                <FormControl fullWidth sx={{ mt: 2 }}>
                    <InputLabel id="categories-label">Categories</InputLabel>
                    <Select
                        labelId="categories-label"
                        multiple
                        value={selectedCategories}
                        onChange={handleChangeCategories}
                        input={<OutlinedInput id="select-multiple-chip" label="Categories" />}
                        renderValue={(selected) => (
                            <div>
                                {selected.map((value) => (
                                    <Chip key={value} label={value} />
                                ))}
                            </div>
                        )}
                        MenuProps={MenuProps}
                    >
                        {categories.map((category) => (
                            <MenuItem key={category} value={category}>
                                {category}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose}>Cancel</Button>
                <Button onClick={handleSubmit}>Create</Button>
            </DialogActions>

        </Dialog>
    );
};

export default CreateMeterDialog;
