import React, { useState, useEffect } from 'react';
import {useNavigate, useParams} from 'react-router-dom';
import axios from 'axios';
import {
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    Box,
    MenuItem,
    FormControl,
    Select,
    Alert,
    InputLabel, Tooltip, CircularProgress, IconButton
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";
import AddBridgeFormDialogue from "../components/AddBridgeFormDialogue";
import CloseIcon from '@mui/icons-material/Close';
import BridgeList from "../components/BridgeList";
import ConfirmDeleteDialog from "../components/ConfirmDeleteDialogue";

const DeviceDetailsPage = () => {
    // general variables
    const [isLoading, setIsLoading] = useState(false);
    const [isDeleteLoading, setIsDeleteLoading] = useState(false);

    const [alert, setAlert] = useState({ show: false, type: '', message: '' });
    // Variables For the First Card

    const { deviceIp } = useParams();
    const navigate = useNavigate();
    const [device, setDevice] = useState(null);
    const [originalDevice, setOriginalDevice] = useState(null);
    const [isEdited, setIsEdited] = useState(false);
    const osOptions = [
        { value: 'ubuntu_20_server', label: 'Ubuntu 20.04 Server' },
    ];
    const ovsEnabledOptions = [
        { value: true, label: 'Enabled' },
        { value: false, label: 'Disabled' },
    ];
    const [oldIpAddress, setOldIpAddress] = useState('');
    const handleEditBridge = (bridge) => {
        console.log("Edit", bridge);
        // Open a dialog or navigate to a page for editing the bridge
    };

    const handleDeleteBridge = (bridge) => {
        console.log("Delete", bridge);
        // Call an API to delete the bridge or handle it as needed
    };


    const deviceTypeOptions = [
        { value: 'switch', label: 'Switch' },
        { value: 'access_point', label: 'Access Point' },
        { value: 'server', label: 'Server' },
    ];

    // *--- Variables for the second card ---*
    const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
    const [bridgeToDelete, setBridgeToDelete] = useState(null);
    const [bridges, setBridges] = useState([]);
    const [bridgesFetched, setBridgesFetched] = useState(false);
    const [openAddBridgeDialog, setOpenAddBridgeDialog] = useState(false);

    // *--- Variables for third card ---*
    const [ports, setPorts] = useState([]);
    const [portsFetched, setPortsFetched] = useState(false);
    const handleOpenDeleteDialogue = (bridge) => {
        setBridgeToDelete(bridge);
        setConfirmDeleteOpen(true);
    };

    const handleCloseDeleteDialog = () => {
        setConfirmDeleteOpen(false);
    };
    const fetchBridges = () => {
        axios.get(`http://localhost:8000/device-bridges/${deviceIp}/`)
            .then(response => {
                const bridgesData = response.data.bridges || [];
                setBridges(bridgesData);
                setBridgesFetched(true);
            })
            .catch(error => console.error('Error fetching bridges:', error));
    };

    const handleConfirmDelete = () => {
        if (bridgeToDelete) {
            setIsDeleteLoading(true); // Enable loading indicator
            axios.post(`http://localhost:8000/delete-bridge/`, {
                lan_ip_address: deviceIp,
                name: bridgeToDelete.name,
            })
                .then(response => {
                    setAlert({
                        show: true,
                        type: 'success',
                        message: `Bridge ${bridgeToDelete.name} deleted successfully.`
                    });
                    fetchBridges(); // Refresh bridges list
                })
                .catch(error => {
                    setAlert({
                        show: true,
                        type: 'error',
                        message: error.response?.data?.message || 'Failed to delete bridge.'
                    });
                })
                .finally(() => {
                    setIsDeleteLoading(false); // Disable loading indicator
                    setConfirmDeleteOpen(false); // Close confirmation dialog
                });
        }
    };

    useEffect(() => {
        setOldIpAddress(deviceIp)
        // Device details for the first card
        axios.get(`http://localhost:8000/device-details/${deviceIp}/`)
            .then(response => {
                setDevice(response.data.device);
                setOriginalDevice(response.data.device);
                console.log(response.data.device);
            })
            .catch(error => console.error('Error fetching device:', error));

        // Fetch Bridges for the second card
        // axios.get(`http://localhost:8000/get-bridges/${deviceIp}/`)
        //     .then(response => {
        //         if (response.data.status === 'success') {
        //             console.log(response.data);
        //         }
        //         // setBridgesFetched(true);
        //     })
        //     .catch(error => console.error('Error fetching bridges:', error));
        // DB bridges
        fetchBridges();
        // axios.get(`http://localhost:8000/device-bridges/${deviceIp}/`)
        //     .then(response => {
        //         console.log(response.data.bridges)
        //         // Check if bridges data exists and is not null, otherwise set to empty array
        //         const bridgesData = response.data.bridges || [];
        //         console.log(bridgesData); // Debugging line
        //         setBridges(bridgesData);
        //         setBridgesFetched(true);
        //     })
        //     .catch(error => console.error('Error fetching bridges:', error));


        // Fetch ports for third card
        axios.get(`http://localhost:8000/device-ports/${deviceIp}/`)
            .then(response => {
                if (response.data.status === 'success') {
                    if (response.data.ports == null) {
                        setPorts([]);
                        console.log('here')
                    } else {
                        setPorts(response.data.ports);
                    }
                }
                setPortsFetched(true);
            })
            .catch(error => console.error('Error fetching ports:', error));
    }, [deviceIp]);

    // *--- Methods for the first card ---*
    const handleChange = (event) => {
        setDevice({ ...device, [event.target.name]: event.target.value });
        setIsEdited(true);
    };
    const handleApply = () => {
        if (!isEdited) return;

        axios.put(`http://localhost:8000/update-device/${oldIpAddress}/`, device)

            .then(response => {
                // navigate('/devices'); // Redirect or handle as needed
                setIsLoading(true)

                if (response.data.status === 'success') {
                    setIsLoading(false)
                    setAlert({ show: true, type: 'success', message: 'Device edited successfully' });
                }
            })
            .catch(error => {
                console.error('Error updating device:', error);
                setAlert({ show: true, type: 'error', message: error });
            });
    };
    if (!device) return <div>Loading...</div>;
    const handleCancel = () => {
        navigate('/devices'); // Redirect or refresh the page as needed
    };

    // *--- Methods for the second card ---*
    const handleOpenAddBridge = () => {
        setOpenAddBridgeDialog(true);
    };

    const handleCloseAddBridge = () => {
        setOpenAddBridgeDialog(false);
        fetchBridges();

    };
    const handleClose = () => {
        setAlert({ show: false, type: '', message: '' })
    }

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
            <Box sx={{
                flexGrow: 1,
                margin: 4
            }}>
                <Button
                    startIcon={<ArrowBackIcon />}
                    onClick={() => navigate(-1)}
                    sx={{ marginBottom: 2 }}
                >
                    Back
                </Button>
                {alert.show && (
                    <Alert
                        severity={alert.type}
                        action={
                            <IconButton
                                aria-label="close"
                                color="inherit"
                                size="small"
                                onClick={handleClose}
                            >
                                <CloseIcon fontSize="inherit" />
                            </IconButton>
                        }
                    >
                        {alert.message}
                    </Alert>
                )}
                <Card raised>
                    <CardContent>
                        {isLoading && <CircularProgress />}
                        {!isLoading && (
                            <div>
                        <Typography variant="h1" component="div" sx={{ marginBottom: 2 }}>
                            {device.name}
                            {/* Add Icon next to name */}
                        </Typography>

                        {Object.keys(device).map(key => (
                            <Box key={key} sx={{ marginBottom: 2 }}>
                                {key === 'os_type' ? (
                                    <FormControl fullWidth>
                                        <InputLabel>Operating System</InputLabel>
                                        <Select
                                            name="os_type"
                                            value={device.os_type}
                                            label="Operating System"
                                            onChange={handleChange}
                                        >
                                            {osOptions.map(option => (
                                                <MenuItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                ) : key === 'device_type' ? (
                                    <FormControl fullWidth>
                                        <InputLabel>Device Type</InputLabel>
                                        <Select
                                            name="device_type"
                                            value={device.device_type}
                                            label="Device Type"
                                            onChange={handleChange}
                                        >
                                            {deviceTypeOptions.map(option => (
                                                <MenuItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                ) : key === 'ovs_enabled' ? (
                                    <FormControl fullWidth>
                                        <InputLabel>OVS Status</InputLabel>
                                        <Select
                                            name="ovs_enabled"
                                            value={device.ovs_enabled}
                                            label="OVS Status"
                                            onChange={handleChange}
                                        >
                                            {ovsEnabledOptions.map(option => (
                                                <MenuItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                ) : (
                                    <TextField
                                        label={key}
                                        name={key}
                                        value={device[key] != null ? device[key] : ''}
                                        onChange={handleChange}
                                        fullWidth
                                    />
                                )

                                }
                            </Box>
                        ))}

                        <Button color="button_green" onClick={handleApply} disabled={!isEdited}>
                            Apply
                        </Button>
                        <Button color="button_red"  onClick={handleCancel} sx={{ marginLeft: 2 }}>
                            Cancel
                        </Button>
        </div>
            )}
                    </CardContent>
                </Card>

                {/*The device's bridges */}
                {device.ovs_enabled && (
                    <Card raised sx={{ marginTop: 4 }}>
                        <CardContent>
                            <ConfirmDeleteDialog
                                open={confirmDeleteOpen}
                                handleClose={handleCloseDeleteDialog}
                                handleConfirm={handleConfirmDelete}
                                itemName="bridge" // Customizing the dialog's message
                                isLoading={isDeleteLoading} // Pass isLoading state to the dialog
                            />
                            <Typography variant="h1" component="div" sx={{ marginBottom: 2 }}>
                                Bridges
                            </Typography>
                            {
                                bridgesFetched ? (
                                    bridges.length > 0 ? (
                                        <BridgeList bridges={bridges} onEdit={handleEditBridge} onDelete={handleOpenDeleteDialogue}  />
                                    ) : (
                                        <Box>
                                            <Typography variant="body_dark" component="div">
                                                There are no OVS bridges assigned to this device.
                                            </Typography>
                                        </Box>
                                    )
                                ) : (
                                    <Typography>Loading bridges...</Typography>
                                )
                            }
                            <AddBridgeFormDialogue
                                deviceIp={deviceIp}
                                onDialogueClose={fetchBridges} // Pass fetchBridges as a prop to be called on dialog close or after successful submission
                            />
                        </CardContent>
                    </Card>
                )}


                {/*<Card raised sx={{ marginTop: 4 }}>
                    <CardContent>
                        <Typography variant="h1" component="div" sx = {{ marginBottom: 2 }}>
                            Ports
                        </Typography>
                        {portsFetched ? (
                            ports.length > 0 ? (
                                ports.map(port => (
                                    <Typography key={port.name}>
                                        {port.name}

                                    </Typography>
                                ))
                            ) : (
                                <Box>
                                    <Typography variant="body_dark" component="div">
                                        There are no ports assigned to this device.
                                    </Typography>
                                    <Button variant='contained' sx={{marginTop: 4 }}>
                                        Add Ports
                                    </Button>
                                </Box>

                            )
                        ) : (
                            <Typography>Loading ports...</Typography>
                        )}
                    </CardContent>
                </Card>*/}
            </Box>
            <Footer />

        </Box>
    );
};

export default DeviceDetailsPage;
