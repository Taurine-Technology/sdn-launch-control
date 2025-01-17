/**
 * File: DeviceStatsGrid.jsx
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
