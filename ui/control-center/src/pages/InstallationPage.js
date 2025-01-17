/**
 * File: InstallationPage.js
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
import SoftwareList from "../components/lists/SoftwareList";

const InstallationPage = () => {
    const [softwares, setSoftwares] = useState([]);

    useEffect(() => {
        setSoftwares([
            {
                title: "Open vSwitch",
                shortDescription: "Virtual multilayer switch to enable network automation.",
                longDescription: "Open vSwitch provides a switching stack that is well-suited for environments with dynamic or automated network conditions. It is designed to support distribution across multiple physical servers similar to VMware's vNetwork distributed vswitch or Cisco's Nexus 1000V.",
                endpoint: "install-ovs"
            },
            {
                title: "ONOS",
                shortDescription: "Open Network Operating System for SDN.",
                longDescription: "ONOS provides the control plane for a software-defined network (SDN), offering high availability, scalability, and performance. It is designed to be a distributed SDN OS for managing network devices.",
                endpoint: "install-controller/onos"
            },
            // Add more software items as needed
        ]);
    }, []);

    const handleInstall = (software) => {
        console.log(`Installing ${software.title}`);
        // Implement installation logic here
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
            <Box sx={{ flexGrow: 1, p: 3 }}>
                <Typography variant="h4" sx={{ mb: 2, color: '#FFFFFF' }}>System: Install Software</Typography>
                <SoftwareList softwares={softwares} onInstall={handleInstall} />
            </Box>
            <Footer />
        </Box>
    );
};

export default InstallationPage;
