import React, { useEffect, useState } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert,
    Button
} from '@mui/material';
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";
import axios from "axios";
import CreateMeterDialog from "../components/onos/MeterCreationDialogue";

const OnosClassifierPage = () => {
    const [controllers, setControllers] = useState([]);
    const [selectedController, setSelectedController] = useState('');
    const [devices, setDevices] = useState([]);
    const [meters, setMeters] = useState([]);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [currentDeviceId, setCurrentDeviceId] = useState('');

    const handleOpenDialog = (deviceId) => {
        setCurrentDeviceId(deviceId);
        setIsDialogOpen(true);
    };

    const handleCloseDialog = () => {
        setIsDialogOpen(false);
        fetchMeters(currentDeviceId, selectedController);
    };
    useEffect(() => {
        const fetchControllers = async () => {
            try {
                const response = await axios.get('http://localhost:8000/controllers/onos/');
                if (response.data.length > 0) {
                    setControllers(response.data);
                    setSelectedController(response.data[0]);  // Default to the first controller
                    fetchDevices(response.data[0]);
                }
            } catch (error) {
                console.error('Failed to fetch controllers:', error);
                setControllers([]);
            }
        };
        fetchControllers();
    }, []);

    const fetchDevices = async (controllerIP) => {
        try {
            const response = await axios.get(`http://localhost:8000/onos/devices/${controllerIP}/`);
            if (response.data && response.data.devices) {
                setDevices(response.data.devices);
                response.data.devices.forEach(device => {
                    fetchMeters(device.id, controllerIP);
                });
            } else {
                setDevices([]);
            }
        } catch (error) {
            console.error('Error fetching devices:', error);
            setDevices([]);
        }
    };

    const fetchMeters = async (deviceId,controllerIP) => {
        try {
            const response = await axios.get(`http://localhost:8000/onos/meters/${controllerIP}/${deviceId}/`);
            if (response.data && response.data.meters) {
                setMeters(prevMeters => ({ ...prevMeters, [deviceId]: response.data.meters }));
            } else {
                setMeters(prevMeters => ({ ...prevMeters, [deviceId]: [] }));
            }
        } catch (error) {
            console.error('Error fetching meters:', error);
            setMeters(prevMeters => ({ ...prevMeters, [deviceId]: [] }));
        }
    };


    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: '#7456FD',
                paddingTop: '100px',
                paddingBottom: '50px',
            }}
        >
            <NavBar />

            <Box sx={{ overflowY: 'auto', flexGrow: 1, p: 3, color: "#FFF" }}>
                <Typography variant="h4" sx={{ mb: 2 }}>AI Services: ONOS Classifier Plugin</Typography>

                <FormControl fullWidth sx={{ mb: 4 }}>
                    <InputLabel id="controller-select-label">Select Controller</InputLabel>
                    <Select
                        labelId="controller-select-label"
                        value={selectedController}
                        onChange={(event) => {
                            setSelectedController(event.target.value);
                            fetchDevices(event.target.value);
                        }}
                    >
                        {controllers.map((controller, index) => (
                            <MenuItem key={index} value={controller}>{controller}</MenuItem>
                        ))}
                    </Select>
                </FormControl>

                {devices.map((device, index) => (
                    <Card key={index} sx={{ mb: 2, backgroundColor: "#02032F", color: "#fff" }}>
                        <CardContent>
                            <Typography variant="h6">Meter Entries for Device {device.id}</Typography>
                            <ul>
                                {meters[device.id] && meters[device.id].map((meter, idx) => (
                                    <li key={idx}>
                                        Switch IP: {meter.ip}, Meter ID: {meter.id}, Meter Type: {meter.type}, Rate: {meter.rate} {meter.unit}, Meter State: {meter.state}
                                    </li>
                                ))}
                            </ul>
                            <Button variant="contained" color="primary" onClick={() => handleOpenDialog(device.id)}>
                                Add Meter
                            </Button>
                        </CardContent>
                    </Card>
                ))}
                <CreateMeterDialog
                    open={isDialogOpen}
                    handleClose={handleCloseDialog}
                    controllerIP={selectedController}
                    deviceId={currentDeviceId}
                />


            </Box>
            <Footer />
        </Box>
    );
};

export default OnosClassifierPage;
