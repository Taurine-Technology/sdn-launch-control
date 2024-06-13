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
        // Split meterCategories only if it's a non-empty string
        setSelectedCategories(meterCategories ? meterCategories.split(',') : []);
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
            setResponseMessage(error.message);
            setResponseType('error')
            if (error.message === "Request failed with status code 400") {
                setResponseMessage('This meter cannot be found.');
                setResponseType('error')
            }
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
