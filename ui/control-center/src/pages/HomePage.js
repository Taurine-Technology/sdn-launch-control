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
