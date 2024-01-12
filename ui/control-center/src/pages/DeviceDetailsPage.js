import React, { useState, useEffect } from 'react';
import {useNavigate, useParams} from 'react-router-dom';
import axios from 'axios';
import {
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    Box,
    MenuItem,
    FormControl,
    Select,
    InputLabel
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";

const DeviceDetailsPage = () => {
    const { deviceIp } = useParams();
    const navigate = useNavigate();
    const [device, setDevice] = useState(null);
    const [originalDevice, setOriginalDevice] = useState(null);
    const [isEdited, setIsEdited] = useState(false);
    const osOptions = [
        { value: 'ubuntu_20_server', label: 'Ubuntu 20.04 Server' },
    ];

    const deviceTypeOptions = [
        { value: 'switch', label: 'Switch' },
        { value: 'access_point', label: 'Access Point' },
        { value: 'server', label: 'Server' },
    ];
    useEffect(() => {
        axios.get(`http://localhost:8000/device-details/${deviceIp}/`)
            .then(response => {
                setDevice(response.data.device);
                setOriginalDevice(response.data.device);
            })
            .catch(error => console.error('Error fetching device:', error));
    }, [deviceIp]);

    const handleChange = (event) => {
        setDevice({ ...device, [event.target.name]: event.target.value });
        setIsEdited(true);
    };
    const handleApply = () => {
        if (!isEdited) return;

        axios.put(`http://localhost:8000/edit-device/${deviceIp}`, device)
            .then(response => {
                navigate('/devices'); // Redirect or handle as needed
            })
            .catch(error => {
                console.error('Error updating device:', error);
            });
    };
    if (!device) return <div>Loading...</div>;
    const handleCancel = () => {
        navigate('/devices'); // Redirect or refresh the page as needed
    };
    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: '#7456FD',
            }}
        >
            <NavBar />
            <Box sx={{
                flexGrow: 1,
                margin: 4
            }}>
                <Button
                    startIcon={<ArrowBackIcon />}
                    onClick={() => navigate(-1)}
                    sx={{ marginBottom: 2 }}
                >
                    Back
                </Button>
                <Card raised>
                    <CardContent>
                        <Typography variant="h5" component="div">
                            {device.name}
                            {/* Add Icon next to name */}
                        </Typography>

                        {Object.keys(device).map(key => (
                            <Box key={key} sx={{ marginBottom: 2 }}>
                                {key === 'os_type' ? (
                                    <FormControl fullWidth>
                                        <InputLabel>Operating System</InputLabel>
                                        <Select
                                            name="os_type"
                                            value={device.os_type}
                                            label="Operating System"
                                            onChange={handleChange}
                                        >
                                            {osOptions.map(option => (
                                                <MenuItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                ) : key === 'device_type' ? (
                                    <FormControl fullWidth>
                                        <InputLabel>Device Type</InputLabel>
                                        <Select
                                            name="device_type"
                                            value={device.device_type}
                                            label="Device Type"
                                            onChange={handleChange}
                                        >
                                            {deviceTypeOptions.map(option => (
                                                <MenuItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                ) : (
                                    <TextField
                                        label={key}
                                        name={key}
                                        value={device[key] != null ? device[key] : ''}
                                        onChange={handleChange}
                                        fullWidth
                                    />
                                )}
                            </Box>
                        ))}

                        <Button color="button_green" onClick={handleApply} disabled={!isEdited}>
                            Apply
                        </Button>
                        <Button color="button_red"  onClick={handleCancel} sx={{ marginLeft: 2 }}>
                            Cancel
                        </Button>
                    </CardContent>
                </Card>
            </Box>
            <Footer />
        </Box>
    );
};

export default DeviceDetailsPage;
