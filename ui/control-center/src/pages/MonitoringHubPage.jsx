/**
 * File: MonitoringHubPage.jsx
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
import { Box, Typography, CircularProgress } from '@mui/material';
import axios from 'axios';
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";
import ClassificationGraph from "../components/ClassificationGraph";
import DeviceStatsGrid from "../components/DeviceStatsGrid";

const MonitoringHub = () => {
    const [hasDevices, setHasDevices] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const checkPluginInstallation = async () => {
            try {
                // Adjust the URL and payload as needed to match your API endpoint for checking the plugin status
                const response = await axios.get('http://localhost:8000/plugins/check/tau-traffic-classification-sniffer/');
                setHasDevices(response.data.hasDevices);
            } catch (error) {
                console.error('Error checking plugin installation:', error);
            } finally {
                setIsLoading(false);
            }
        };

        checkPluginInstallation();
    }, []);

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

            <Box sx={{ overflowY: 'auto', flexGrow: 1, p: 2 }}>
                <Typography variant="h2" sx={{ mb: 2, color: "#FFF" }}>Monitoring: Hub</Typography>
                {isLoading ? (
                    <CircularProgress color="inherit" />
                ) : hasDevices ? (
                        <>
                    <ClassificationGraph />
                    <DeviceStatsGrid />
                    </>
                ) : (
                    <DeviceStatsGrid />
                )}
            </Box>
            <Footer />
        </Box>
    );
};

export default MonitoringHub;
