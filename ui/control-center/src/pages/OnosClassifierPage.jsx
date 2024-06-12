import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Select, MenuItem, FormControl, InputLabel, Alert } from '@mui/material';
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";
import axios from "axios";

const OnosClassifierPage = () => {
    const [controllers, setControllers] = useState([]);
    const [selectedController, setSelectedController] = useState('');
    const [meters, setMeters] = useState([]);

    const handleControllerChange = async (event) => {
        const selectedIP = event.target.value;
        setSelectedController(selectedIP);
        fetchMeters(selectedIP);
    };

    useEffect(() => {
        const fetchControllers = async () => {
            try {
                const response = await axios.get('http://localhost:8000/controllers/onos/');
                if (response.data.length > 0) {
                    setControllers(response.data);
                    setSelectedController(response.data[0]);  // Default to the first controller
                    fetchMeters(response.data[0]);
                }
            } catch (error) {
                console.error('Failed to fetch controllers:', error);
                setControllers([]);
            }
        };
        fetchControllers();
    }, []);

    const fetchMeters = async (controllerIP) => {
        try {
            const response = await axios.get(`http://localhost:8000/onos/meters/${controllerIP}/`);
            if (response.data && response.data.meters) {
                const metersByDevice = groupMetersByDevice(response.data.meters);
                setMeters(metersByDevice);
            } else {
                setMeters([]);
            }
        } catch (error) {
            console.error('Error fetching meters:', error);
            setMeters([]);
        }
    };

    const groupMetersByDevice = (meters) => {
        return meters.reduce((acc, meter) => {
            (acc[meter.device_id] = acc[meter.device_id] || []).push(meter);
            return acc;
        }, {});
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

                {controllers.length > 0 ? (
                    <FormControl fullWidth sx={{ mb: 4 }}>
                        <InputLabel id="controller-select-label">Select Controller</InputLabel>
                        <Select
                            labelId="controller-select-label"
                            value={selectedController}
                            onChange={handleControllerChange}
                        >
                            {controllers.map((controller, index) => (
                                <MenuItem key={index} value={controller}>{controller}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                ) : (
                    <Alert severity="info">No ONOS controllers available. Please add a controller to manage features.</Alert>
                )}

                {Object.keys(meters).length > 0 ? (
                    Object.entries(meters).map(([deviceId, deviceMeters], index) => (
                        <Card key={index} sx={{ mb: 2, backgroundColor: "#02032F", color: "#fff" }}>
                            <CardContent>
                                <Typography variant="h6">Meter Entries for Device {deviceId}</Typography>
                                <ul>
                                    {deviceMeters.map((meter, idx) => (
                                        <li key={idx}>
                                            Switch IP: {meter.ip}, Meter ID: {meter.id}, Meter Type: {meter.type}, Rate: {meter.rate} {meter.unit}, Meter State: {meter.state}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    ))
                ) : (
                    <Alert severity="info">No meter entries available for the selected controller.</Alert>
                )}
            </Box>
            <Footer />
        </Box>
    );
};

export default OnosClassifierPage;
