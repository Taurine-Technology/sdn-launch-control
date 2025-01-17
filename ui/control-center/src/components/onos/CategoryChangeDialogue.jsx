/**
 * File: CategoryChangeDialogue.jsx
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
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, FormControl, InputLabel, Select, MenuItem, Chip, OutlinedInput } from '@mui/material';
import axios from "axios";
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
const ManageCategoriesDialog = ({ open, onClose, categories, meterCategories, meter }) => {
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState(''); // 'success' or 'error'
    const [selectedCategories, setSelectedCategories] = useState([]);

    useEffect(() => {
        console.log(meterCategories)
        // Split meterCategories only if it's a non-empty string
        setSelectedCategories(meterCategories ? meterCategories : []);
    }, [meterCategories]);

    const submit = async () => {
        try {
            const cats = selectedCategories.join(',')
            const response = await axios.post('http://localhost:8000/update_meter/', {
                meter_id: meter.id,
                categories: cats
            })
            setResponseMessage('Successfully updated meter');
            setResponseType('success')
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

    const handleChange = (event) => {
        setSelectedCategories(event.target.value);
    };
    const handleCloseAlert = () => {
        setResponseMessage('')
    }


    return (
        <Dialog open={open} onClose={onClose} PaperProps={{
            style: {
                minWidth: '500px', // You can use numeric values or strings with valid CSS units
            }
        }}>
            <DialogTitle>Manage Meter Categories</DialogTitle>
            {responseMessage && (
                <Alert severity={responseType} onClose={handleCloseAlert}>
                    {responseMessage}
                </Alert>
            )}
            <DialogContent>
                <FormControl fullWidth>
                    <InputLabel id="demo-multiple-chip-label">Categories</InputLabel>
                    <Select
                        labelId="demo-multiple-chip-label"
                        multiple
                        value={selectedCategories}
                        onChange={handleChange}
                        input={<OutlinedInput id="select-multiple-chip" label="Chip" />}
                        renderValue={(selected) => (
                            <div>
                                {selected.map((value) => (
                                    <Chip key={value} label={value} />
                                ))}
                            </div>
                        )}
                        MenuProps={MenuProps}
                    >
                        {categories.map((name) => (
                            <MenuItem key={name} value={name}>
                                {name}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cancel</Button>
                <Button onClick={submit}>Save</Button>
            </DialogActions>
        </Dialog>
    );
};

export default ManageCategoriesDialog;
