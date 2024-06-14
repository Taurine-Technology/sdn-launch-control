import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Grid, Card, CardContent, Typography } from '@mui/material';
import DeviceStatsGraph from "./DeviceStatsGraph";

const DeviceStatsGrid = () => {
    const [targetIpAddresses, setTargetIpAddresses] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Fetch devices from the backend
        const fetchDevices = async () => {
            try {
                const response = await axios.get('http://localhost:8000/devices/');
                const switches = response.data.filter(device => device.device_type === 'switch');
                const ips = switches.map(switchDevice => switchDevice.lan_ip_address);
                setTargetIpAddresses(ips);
            } catch (error) {
                console.error('Failed to fetch devices', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchDevices();
    }, []);

    if (isLoading) {
        return (
            <Card raised sx={{ margin: 4, bgcolor: '#02032F' }}>
                <CardContent>
                    <Typography>Loading devices...</Typography>
                </CardContent>
            </Card>
        );
    }

    if (targetIpAddresses.length === 0) {
        return (
            <Card raised sx={{ margin: 4, bgcolor: '#02032F' }}>
                <CardContent>
                    <Typography>No switches connected. Please connect a switch to monitor.</Typography>
                </CardContent>
            </Card>
        );
    }

    return (
        <Grid container spacing={2}>
            {targetIpAddresses.map(ip => (
                <Grid item xs={12} md={6} key={ip}>
                    <DeviceStatsGraph targetIpAddress={ip} />
                </Grid>
            ))}
        </Grid>
    );
};

export default DeviceStatsGrid;
