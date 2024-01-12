import React, {useState} from 'react';
import NavBar from "../components/NavBar";
import Box from "@mui/material/Box";
import Footer from "../components/Footer";
import Button from '@mui/material/Button';
import InstallOvsFormDialogue from "../components/InstallOvsFormDialogue";
const HomePage = () => {
    const [isTerminalOpen, setIsTerminalOpen] = useState(false);

    // const toggleTerminal = () => {
    //     setIsTerminalOpen(!isTerminalOpen);
    // };
    //
    // const sshConfig = {
    //     host: '10.0.0.17',
    //     port: 22,
    //     username: 'inethi',
    //     password: 'inethi'
    // };

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
                <InstallOvsFormDialogue />
                {/*<Terminal isOpen={isTerminalOpen} sshConfig={sshConfig} />*/}
                {/*<Button variant="contained" onClick={toggleTerminal} sx={{ margin: 2}}>*/}
                {/*    {isTerminalOpen ? 'Close Terminal' : 'Open Terminal'}*/}
                {/*</Button>*/}

                {/* Main content of the HomePage goes here */}
            </Box>
            <Footer />
        </Box>
    );
}

export default HomePage