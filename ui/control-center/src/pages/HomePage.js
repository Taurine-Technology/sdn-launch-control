import React, {useState} from 'react';
import NavBar from "../components/NavBar";
import {Box, Card, CardContent, Stack} from '@mui/material';
import Footer from "../components/Footer";
import NetworkDiagram from "../components/NetworkDiagram";
import Button from '@mui/material/Button';
import InstallFormDialogue from "../components/InstallFormDialogue";
const HomePage = () => {
    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: '#7456FD',
            }}
        >
            <NavBar />
                    <NetworkDiagram />
            <Box
                sx={{
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                }}
            >
                <Stack
                    direction="row"
                    spacing={4}
                    sx={{
                        width: '100%', // Ensures Stack takes full width of its parent
                        maxWidth: '600px',
                        alignItems: 'center', // Centers the children horizontally
                        marginBottom: 2
                    }}
                >
                    <InstallFormDialogue installationType="Open vSwitch" endpoint="install-ovs" />
                    <InstallFormDialogue installationType="ONOS" endpoint="install-onos" />

                </Stack>

            </Box>
            <Footer />
        </Box>
    );
};

export default HomePage;