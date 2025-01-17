/**
 * File: HomePage.js
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

import React from 'react';
import {Box, Typography} from '@mui/material';
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";
import OvsNetworkDiagram from "../components/OvsNetworkDiagram";
import ClassificationGraph from "../components/ClassificationGraph";

const HomePage = () => {

    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: '#7456FD',
                paddingTop: '100px', // Adjust this based on your Navbar height
                paddingBottom: '50px', // Adjust this based on your Footer height
            }}
        >
            <NavBar />

            <Box sx={{ overflowY: 'auto', flexGrow: 1, p: 3}}>
                <Typography variant="h1" sx={{ mb: 2, color: "#FFF" }}>Lobby: Dashboard</Typography>
                <OvsNetworkDiagram />

            </Box>
            <Footer />
        </Box>
    );
};

export default HomePage;
