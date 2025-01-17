/**
 * File: MeterChangeDialogue.jsx
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
            console.log(selectedCategories)
            const payload = {
                controller_ip: controllerIP,
                switch_id: deviceId,
                rate: rate,
                categories: selectedCategories
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
            if (error.response && error.response.data) {
                // Check if the backend sent a specific error message and display it
                setResponseMessage(error.response.data.error || 'An unexpected error occurred');
            } else {
                // Generic error message if the response doesn't contain detailed info
                setResponseMessage('Failed to create meter due to a network or server error.');
            }
            setResponseType('error');
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
