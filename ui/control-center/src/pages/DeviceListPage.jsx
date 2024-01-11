import React, {useEffect, useState} from 'react';
import NavBar from "../components/NavBar";
import Box from "@mui/material/Box";
import Footer from "../components/Footer";
import ConfirmDeleteDialog from "../components/ConfirmDeleteDialogue";
import Alert from '@mui/material/Alert';
import EditDeviceDialogue from "../components/EditDeviceDialogue";
import axios from "axios";
import DeviceList from "../components/DeviceList";
import Theme from "../theme";
import EditDeviceDialog from "../components/EditDeviceDialogue";
import {ThemeProvider} from "@mui/material/styles";
import theme from "../theme";
import InternalServerErrorDialogue from "../components/InternalServerErrorDialogue";

const DeviceListPage = () => {
    const [openDeleteDialogue, setOpenDeleteDialogue] = useState(false);
    const [deviceToDelete, setDeviceToDelete] = useState(null);
    const [devices, setDevices] = useState([]);
    const [alert, setAlert] = useState({ show: false, message: '' });
    const [successAlert, setSuccessAlert] = useState({ show: false, message: '' });
    const [openEditDialogue, setOpenEditDialogue] = useState(false);
    const [deviceToEdit, setDeviceToEdit] = useState({ name: '', ip_address: '', device_type: '' });
    const [openAddDialog, setOpenAddDialog] = useState(false);
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState(''); // 'success' or 'error'
    const [error, setError] = useState(null);
    const handleCloseAlert = () => {
        setResponseMessage('');
    };
    const handleDeleteClick = (device) => {
        setDeviceToDelete(device);
        setOpenDeleteDialogue(true);
    };

    const handleCloseDeleteDialog = () => {
        setOpenDeleteDialogue(false);
    };

    const handleConfirmDelete = async () => {
        if (deviceToDelete) {
            try {

                const payload = {
                    lan_ip_address: deviceToDelete.lan_ip_address,
                    wireguard_ip_address: deviceToDelete.wireguard_ip_address
                };

                const response = await axios.delete('http://localhost:8000/delete-device/', { data: payload });

                setDevices(devices.filter(device => device.lan_ip_address !== deviceToDelete.lan_ip_address && device.wireguard_ip_address !== deviceToDelete.wireguard_ip_address));
                setResponseMessage('Successfully deleted device.');
                setResponseType('success');
            } catch (error) {
                // console.error('Error deleting device:', error);
                setResponseMessage(`Failed to delete device: ${error.message}`);
                setResponseType('error');
            }
        }
        setOpenDeleteDialogue(false);
        setDeviceToDelete(null);
    };


    const handleUpdateDevice = (oldIpAddress, updatedDevice) => {
        console.log('We are editing...');
        setOpenEditDialogue(false);

    };
    const handleEditClick = (device) => {
        setDeviceToEdit(device);
        console.log(device)
        setOpenEditDialogue(true);
    };

    const handleCloseEditDialogue = () => {
        setOpenEditDialogue(false);
    };
    useEffect(() => {
        const fetchDevices = async () => {
            try {
                const response = await axios.get('http://localhost:8000/devices/');
                setDevices(response.data); // Axios automatically handles JSON parsing
                console.log(response.data)
            } catch (error) {
                console.error('Error fetching devices:', error);
                setError(error.message);
            }
        };

        fetchDevices();
    }, []);
    const handleClose = () => {
        // Reset the error state to null
        setError(null);
    };
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
                {responseMessage && (
                    <Alert severity={responseType} onClose={handleCloseAlert}>
                        {responseMessage}
                    </Alert>
                )}
                <InternalServerErrorDialogue
                    open={error != null}
                    errorMessage={'There has been an internal error. Please contact support.'}
                    onClose={handleClose}
                />
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

                        <DeviceList devices={devices} onDelete={handleDeleteClick} onEdit={handleEditClick}/>
                        <ConfirmDeleteDialog
                            open={openDeleteDialogue}
                            handleClose={handleCloseDeleteDialog}
                            handleConfirm={handleConfirmDelete}
                        />
                        <EditDeviceDialog
                            open={openEditDialogue}
                            handleClose={handleCloseEditDialogue}
                            device={deviceToEdit}
                            handleUpdate={handleUpdateDevice}
                        />
                    </Box>

                </Box>
                <Footer />
            </Box>

    );
}

export default DeviceListPage