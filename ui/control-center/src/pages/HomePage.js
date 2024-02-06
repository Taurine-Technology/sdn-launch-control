import React, {useState} from 'react';
import NavBar from "../components/NavBar";
import { Box, Stack } from '@mui/material';
import Footer from "../components/Footer";
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
                    direction="column"
                    spacing={2} // Adjust spacing as needed
                    sx={{
                        width: '100%', // Ensures Stack takes full width of its parent
                        maxWidth: '600px', // Adjust maximum width as needed
                        alignItems: 'center', // Centers the children horizontally
                    }}
                >
                    <InstallFormDialogue installationType="Open vSwitch" endpoint="install-ovs" />
                    <InstallFormDialogue installationType="ONOS" endpoint="install-onos" />
                    {/* Add other buttons or content here, wrapped in Stack if needed */}
                </Stack>
                {/* Additional content can go here */}
            </Box>
            <Footer />
        </Box>
    );
};

export default HomePage;