
import React, { useEffect, useState } from 'react';
import NavBar from "../components/NavBar";
import Box from "@mui/material/Box";
import Footer from "../components/Footer";
import Alert from '@mui/material/Alert';
import axios from "axios";
import ControllerList from "../components/ControllerList";
import { ThemeProvider } from "@mui/material/styles";
import theme from "../theme";
import { CircularProgress, Backdrop } from "@mui/material";
import Theme from "../theme";
const ControllerListPage = () => {
    const [controllers, setControllers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchControllers = async () => {
        setLoading(true);
        try {
            const response = await axios.get('http://localhost:8000/controllers/');
            setControllers(response.data);
        } catch (error) {
            console.error('Error fetching controllers:', error);
            setError(error.message || 'An error occurred while fetching controllers.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchControllers();
    }, []);

    const handleClose = () => {
        setError('');
    };

    return (
        <ThemeProvider theme={theme}>
            <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#7456FD', }}>
                <NavBar />
                <Backdrop open={loading} style={{ zIndex: theme.zIndex.drawer + 1 }}>
                    <CircularProgress color="inherit" />
                </Backdrop>
                {error && (
                    <Alert severity="error" onClose={handleClose}>
                        {error}
                    </Alert>
                )}
                <Box
                    sx={{
                        flexGrow: 1,
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'start',
                        padding: Theme.spacing(2), // Add some padding around the list
                        margin: Theme.spacing(2),


                    }}
                >
                    <ControllerList controllers={controllers} />
                </Box>
                <Footer />
            </Box>
        </ThemeProvider>
    );
}

export default ControllerListPage;
