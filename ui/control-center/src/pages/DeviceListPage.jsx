import React, {useEffect, useState} from 'react';
import NavBar from "../components/NavBar";
import Box from "@mui/material/Box";
import Footer from "../components/Footer";
import ConfirmDeleteDialog from "../components/ConfirmDeleteDialogue";
import Alert from '@mui/material/Alert';
import axios from "axios";
import DeviceList from "../components/DeviceList";
import Theme from "../theme";
import EditDeviceDialog from "../components/EditDeviceDialogue";
import {ThemeProvider} from "@mui/material/styles";
import theme from "../theme";
import InternalServerErrorDialogue from "../components/InternalServerErrorDialogue";
import PortManagementDialogue from "../components/PortManagementDialogue";
import { useNavigate } from 'react-router-dom';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import {Backdrop, CircularProgress} from "@mui/material";
import AddDeviceDialogue from "../components/AddDeviceDialogue";

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
    const [openPortDialogue, setOpenPortDialogue] = useState(false)
    const [loading, setLoading] = useState(false);
    const [isDeleteLoading, setIsDeleteLoading] = useState(false);
    const navigate = useNavigate();


        const handleDetailsClick = async (ipAddress) => {
            setLoading(true);
            try {
                const response = await axios.get(`http://localhost:8000/check-connection/${ipAddress}/`);
                if (response.data.status === 'success') {
                    navigate(`/devices/${ipAddress}`);
                } else {
                    // Handle unsuccessful connection check
                    setAlert({ show: true, message: 'Device connection failed.' });
                }
            } catch (error) {
                // Handle error
                console.error('Error:', error || 'Deployment failed');
                setResponseMessage(error.response?.data?.message || error.message || 'Deployment failed');
                setResponseType('error');
            } finally {
                setLoading(false);
            }
        };
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
    const handleCloseAddDevice = () => {
        fetchDevices();
    };

    const handleConfirmDelete = async () => {
        if (deviceToDelete) {
            try {
                setIsDeleteLoading(true);
                const payload = {
                    lan_ip_address: deviceToDelete.lan_ip_address,
                };

                const response = await axios.delete('http://localhost:8000/delete-device/', { data: payload })
                    .then(response =>
                {

                    setResponseMessage('Successfully deleted device.');
                    setResponseType('success');
                    fetchDevices()
                }).catch(error => {
                        setResponseMessage(`Failed to delete device: ${error.message}`);
                        setResponseType('error');
                }).finally(() =>{
                        setIsDeleteLoading(false);
                        setOpenDeleteDialogue(false);
                        setDeviceToDelete(null);
                    });

                // setDevices(devices.filter(device => device.lan_ip_address !== deviceToDelete.lan_ip_address));

            } catch (error) {
                // console.error('Error deleting device:', error);
                setResponseMessage(`Failed to delete device: ${error.message}`);
                setResponseType('error');
            }
        }

    };


    const handleUpdateDevice = async (oldIpAddress, updatedDevice) => {
        console.log('Updating device...');

        try {
            const response = await fetch(`http://localhost:8000/update-device/${oldIpAddress}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updatedDevice),
            });

            const result = await response.json();

            if (response.ok) {
                console.log('Device updated successfully.');
                fetchDevices()
                setResponseMessage('Successfully Updated device.');
                setResponseType('success');
                setOpenEditDialogue(false);
            } else {
                console.error('Failed to update device:', result.message);
                setResponseMessage(`Failed to update device: ${result.message}`);
                setResponseType('error');
                setOpenEditDialogue(false);

            }
        } catch (error) {
            console.error('Error updating device:', error);
            setResponseMessage(`Failed to update device: ${error}`);
            setResponseType('error');
            setOpenEditDialogue(false);

        }
    };
    const handleEditClick = (device) => {
        console.log(device)
        setDeviceToEdit(device);
        console.log(device)
        setOpenEditDialogue(true);
    };
    const handleEditPortClick = (device) => {
        setDeviceToEdit(device);
        console.log(device)
        setOpenPortDialogue(true);
    };

    const handleClosePortDialogue = () => {
        setOpenPortDialogue(false);
    }
    const selectedDeviceForPortManagement = (device) => {
        console.log('selecting ports')
        setDeviceToEdit(device);
        console.log(device)
        setOpenEditDialogue(true);
    }
    const handleCloseEditDialogue = () => {
        setOpenEditDialogue(false);
    };
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
    useEffect(() => {


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
                <Backdrop open={loading} style={{ zIndex: theme.zIndex.drawer + 1 }}>
                    <CircularProgress color="inherit" />
                </Backdrop>

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
                    {responseMessage && (
                        <Alert severity={responseType} onClose={handleCloseAlert}>
                            {responseMessage}
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


                        <DeviceList devices={devices}
                                    onDelete={handleDeleteClick}
                                    onEdit={handleEditClick}
                                    // onEditPorts={handleEditPortClick}
                                    onViewDetails={handleDetailsClick}
                        />
                        <ConfirmDeleteDialog
                            open={openDeleteDialogue}
                            handleClose={handleCloseDeleteDialog}
                            handleConfirm={handleConfirmDelete}
                            itemName='device'
                            isLoading={isDeleteLoading}
                        />
                        <EditDeviceDialog
                            open={openEditDialogue}
                            handleClose={handleCloseEditDialogue}
                            device={deviceToEdit}
                            handleUpdate={handleUpdateDevice}
                        />

                    </Box>
                <AddDeviceDialogue fetchDevices={fetchDevices} />
                </Box>
                <Footer />
            </Box>

    );
}

export default DeviceListPage