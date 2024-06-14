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
