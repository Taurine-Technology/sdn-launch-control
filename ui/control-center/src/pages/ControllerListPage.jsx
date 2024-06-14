
import React, { useEffect, useState } from 'react';
import NavBar from "../components/NavBar";
import Box from "@mui/material/Box";
import Footer from "../components/Footer";
import Alert from '@mui/material/Alert';
import axios from "axios";
import ControllerList from "../components/lists/ControllerList";
import { ThemeProvider } from "@mui/material/styles";
import theme from "../theme";
import {CircularProgress, Backdrop, Typography} from "@mui/material";
import Theme from "../theme";
import ConfirmDeleteDialog from "../components/ConfirmDeleteDialogue";
const ControllerListPage = () => {
    const [controllers, setControllers] = useState([]);
    const [openDeleteDialogue, setOpenDeleteDialogue] = useState(false);
    const [controllerToDelete, setControllerToDelete] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [isDeleteLoading, setIsDeleteLoading] = useState(false);
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState(''); // 'success' or 'error'
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

    const handleDeleteClick = (device) => {
        setControllerToDelete(device);
        setOpenDeleteDialogue(true);
    };

    const handleConfirmDelete = async () => {
        if (controllerToDelete) {
            try {
                setIsDeleteLoading(true);
                const payload = {
                    controller_ip: controllerToDelete.lan_ip_address,
                };

                const response = await axios.delete('http://localhost:8000/delete-controller/', { data: payload })
                    .then(response =>
                    {

                        setResponseMessage('Successfully deleted device.');
                        setResponseType('success');
                        fetchControllers()
                    }).catch(error => {
                        setResponseMessage(`Failed to delete device: ${error.message}`);
                        setResponseType('error');
                    }).finally(() =>{
                        setOpenDeleteDialogue(false);
                        setIsDeleteLoading(false);
                        setControllerToDelete(null);
                    });

                // setDevices(devices.filter(device => device.lan_ip_address !== deviceToDelete.lan_ip_address));

            } catch (error) {
                // console.error('Error deleting device:', error);
                setResponseMessage(`Failed to delete controller: ${error.message}`);
                setResponseType('error');
            }
        }

    };

    const handleCloseDeleteDialog = () => {
        setOpenDeleteDialogue(false);
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
                <Box sx={{ flexGrow: 1, paddingTop: '100px', overflow: 'auto' }}>
                <Typography variant="h1" sx={{ mb: 2, p: 3, color: "#FFF"}}>Hardware: Controllers</Typography>
                <Box
                    sx={{
                        flexGrow: 1,
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'start',

                        margin: Theme.spacing(2),

                        paddingBottom: '50px',

                    }}
                >

                    <ControllerList controllers={controllers} onDelete={handleDeleteClick} />
                    <ConfirmDeleteDialog
                        open={openDeleteDialogue}
                        handleClose={handleCloseDeleteDialog}
                        handleConfirm={handleConfirmDelete}
                        itemName='controller'
                        isLoading={isDeleteLoading}
                    />
                </Box>
                </Box>
                <Footer />
            </Box>
        </ThemeProvider>
    );
}

export default ControllerListPage;
