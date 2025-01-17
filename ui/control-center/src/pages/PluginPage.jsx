/**
 * File: PluginPage.jsx
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

import React, { useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";
import PluginList from "../components/lists/PluginList";
import axios from "axios";

const PluginsPage = () => {
    const [plugins, setPlugins] = useState([]);
    const [error, setError] = useState(null);
    const fetchPlugins = async () => {
        try {
            const response = await axios.get('http://localhost:8000/plugins/');
            setPlugins(response.data);

        } catch (error) {
            console.error('Error fetching devices:', error);
            setError(error.message);
        }
        const hardcodedData = [
            {
                alias: "Traffic Classification Sniffer",
                name: "tau-traffic-classification-sniffer",
                version: "0.0.1",
                short_description: "Traffic sniffer that interfaces with Launch Control's AI models to classify your network traffic in real-time.",
                long_description: "Detailed information about Traffic Classification Sniffer. It offers deep insights into network patterns, enabling efficient data management and security.",
                author: "Taurine Technology",
                installed: "no"
            },
            {
                alias: "ONOS Metres",
                name: "tau-onos-metre-traffic-classification",
                version: "0.0.1",
                short_description: "Create ONOS Metres based on Traffic Classifications",
                long_description: "This plugin allows for the creation of ONOS Metres that can classify traffic based on various parameters, improving network performance and security.",
                author: "Taurine Technology",
                installed: "yes"
            },
        ];

        // setPlugins(hardcodedData);
    };

    useEffect(() => {
        fetchPlugins();
    }, []);

    const handleDelete = (plugin) => {
        console.log('Delete', plugin.name);
    };

    const handleInstall = (plugin) => {
        console.log('Install', plugin.name);
    };

    return (
        <Box sx={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: '#7456FD',
            paddingTop: '100px',
            paddingBottom: '50px',
        }}>
            <NavBar />
            <Box sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
                <Typography variant="h4" sx={{ mb: 2, color: '#FFFFFF' }}>System: Plugins</Typography>
                <PluginList plugins={plugins} onDelete={handleDelete} onInstall={handleInstall} fetchPlugins={fetchPlugins}/>
            </Box>
            <Footer />
        </Box>
    );
};

export default PluginsPage;
