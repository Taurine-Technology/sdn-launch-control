import NavBar from "../components/NavBar";
import {Box, Stack} from '@mui/material';
import Footer from "../components/Footer";
import InstallFormDialogue from "../components/InstallFormDialogue";
import OvsNetworkDiagram from "../components/OvsNetworkDiagram";


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
                    <OvsNetworkDiagram />

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
                    spacing={4}
                    sx={{
                        width: '100%', // Ensures Stack takes full width of its parent
                        maxWidth: '600px',
                        alignItems: 'center', // Centers the children horizontally
                        marginBottom: 2
                    }}>
                    <Stack
                        direction="row"
                        spacing={4}
                        sx={{
                            width: '100%', // Ensures Stack takes full width of its parent
                            maxWidth: '600px',
                            alignItems: 'center', // Centers the children horizontally
                            margin: 2
                        }}
                    >
                        <InstallFormDialogue installationType="Open vSwitch" endpoint="install-ovs" />
                        <InstallFormDialogue installationType="ONOS" endpoint="install-controller/onos" />
                    </Stack>
                    <Stack
                        direction="row"
                        spacing={4}
                        sx={{
                            width: '100%', // Ensures Stack takes full width of its parent
                            maxWidth: '600px',
                            alignItems: 'center', // Centers the children horizontally
                            margin: 2
                        }}
                    >
                        <InstallFormDialogue installationType="Faucet" endpoint="install-controller/faucet" />
                        <InstallFormDialogue installationType="OpenDaylight" endpoint="install-controller/odl" />
                    </Stack>
                </Stack>

            </Box>
            <Footer />
        </Box>
    );
};

export default HomePage;