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
