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
    InputLabel, Tooltip
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";
import AddBridgeFormDialogue from "../components/AddBridgeFormDialogue";

const DeviceDetailsPage = () => {
    // Variables For the First Card
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

    // *--- Variables for the second card ---*
    const [bridges, setBridges] = useState([]);
    const [bridgesFetched, setBridgesFetched] = useState(false);
    const [openAddBridgeDialog, setOpenAddBridgeDialog] = useState(false);

    // *--- Variables for third card ---*
    const [ports, setPorts] = useState([]);
    const [portsFetched, setPortsFetched] = useState(false);


    useEffect(() => {

        // Device details for the first card
        axios.get(`http://localhost:8000/device-details/${deviceIp}/`)
            .then(response => {
                setDevice(response.data.device);
                setOriginalDevice(response.data.device);
            })
            .catch(error => console.error('Error fetching device:', error));

        // Fetch Bridges for the second card
        axios.get(`http://localhost:8000/get-bridges/${deviceIp}/`)
            .then(response => {
                if (response.data.status === 'success') {
                    console.log(response.data);
                }
                // setBridgesFetched(true);
            })
            .catch(error => console.error('Error fetching bridges:', error));
        // DB bridges
        axios.get(`http://localhost:8000/device-bridges/${deviceIp}/`)
            .then(response => {
                if (response.data.status === 'success') {
                    setBridges(response.data.bridges);
                }
                setBridgesFetched(true);
            })
            .catch(error => console.error('Error fetching bridges:', error));

        // Fetch ports for third card
        axios.get(`http://localhost:8000/device-ports/${deviceIp}/`)
            .then(response => {
                if (response.data.status === 'success') {
                    setPorts(response.data.ports);
                }
                setPortsFetched(true);
            })
            .catch(error => console.error('Error fetching ports:', error));
    }, [deviceIp]);

    // *--- Methods for the first card ---*
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

    // *--- Methods for the second card ---*
    const handleOpenAddBridge = () => {
        setOpenAddBridgeDialog(true);
    };

    const handleCloseAddBridge = () => {
        setOpenAddBridgeDialog(false);
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
                        <Typography variant="h1" component="div" sx={{ marginBottom: 2 }}>
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

                {/*The devices bridges. If there are no bridges then a button to add a bridge*/}
                <Card raised sx={{ marginTop: 4 }}>
                    <CardContent>
                      <Typography variant="h1" component="div" sx={{ marginBottom: 2 }}>
                            Bridges
                        </Typography>
                        {bridgesFetched ? (
                            bridges.length > 0 ? (
                                bridges.map(bridge => (
                                    <Typography key={bridge.name}>
                                        {bridge.name}
                                        {/* Add additional bridge details here if needed */}
                                    </Typography>
                                ))
                            ) : (
                                <Box>
                                    <Typography variant="body_dark" component="div">
                                    There are no OVS bridges assigned to this device.
                                    </Typography>

                                </Box>
                            )
                        ) : (
                            <Typography>Loading bridges...</Typography>
                        )}
                        <AddBridgeFormDialogue
                            deviceIp={deviceIp}
                        />

                    </CardContent>
                </Card>

                {/*The devices ports. If there are no ports then a button to add ports*/}
                <Card raised sx={{ marginTop: 4 }}>
                    <CardContent>
                        <Typography variant="h1" component="div" sx = {{ marginBottom: 2 }}>
                            Ports
                        </Typography>
                        {portsFetched ? (
                            ports.length > 0 ? (
                                ports.map(port => (
                                    <Typography key={port.name}>
                                        {port.name}
                                        {/* Add additional port details here if needed */}
                                    </Typography>
                                ))
                            ) : (
                                <Box>
                                    <Typography variant="body_dark" component="div">
                                        There are no ports assigned to this device.
                                    </Typography>
                                    <Button variant='contained' sx={{marginTop: 4 }}>
                                        Add Ports
                                    </Button>
                                </Box>

                            )
                        ) : (
                            <Typography>Loading ports...</Typography>
                        )}
                    </CardContent>
                </Card>
            </Box>
            <Footer />

        </Box>
    );
};

export default DeviceDetailsPage;
