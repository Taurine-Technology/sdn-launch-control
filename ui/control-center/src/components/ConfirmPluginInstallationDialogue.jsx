import React, {useState} from 'react';
import {
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    Button,
    CircularProgress,
    Box
} from '@mui/material';
import axios from "axios";
import Alert from "@mui/material/Alert";

function ConfirmPluginInstallationDialogue({ open, handleClose, itemName = "item", isLoading, pluginName, installed }) {
    const [loading, setLoading] = useState(false);
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState(''); // 'success' or 'error'

    const installPlugin = async () => {
        setLoading(true);

        // Check if the specific plugin requires a pre-condition and is not met
        if (pluginName === 'tau-onos-metre-traffic-classification' && !installed) {
            setResponseType('error');
            setResponseMessage('Please install the Traffic Classification Sniffer to enable this plugin.');
            setLoading(false);
            return;  // Early exit if the condition is not met
        }

        // Proceed to install the plugin if conditions are met or not needed
        try {
            const response = await axios.post(`http://localhost:8000/plugins/install/${pluginName}/`);
            // Handle successful installation response if needed
        } catch (error) {
            console.error('Error installing plugin:', error);
            setResponseType('error');
            setResponseMessage(error.message || 'An error occurred while installing the plugin.');
        } finally {
            setLoading(false);
        }
    };


    const handleCloseError = () => {
        setResponseMessage('');
    };

    return (
        <Dialog open={open} onClose={handleClose} sx={{ '& .MuiDialog-paper': { minWidth: '600px' }} }>
            <DialogTitle>{"Confirm Plugin Installation"}</DialogTitle>
            { (loading ) && (
                <CircularProgress style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex:1000 }} />
            )}
            { responseMessage &&
                (<Alert severity={responseType} onClose={handleCloseError}>
                    {responseMessage}
                </Alert>)
            }
            {isLoading ? (
                <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                    <CircularProgress />
                </Box>
            ) : (

                <DialogContentText sx={{paddingLeft:3}}>
                    Are you sure you want to install {itemName}?
                </DialogContentText>
            )}

            <DialogActions>
                <Button onClick={handleClose} color="button_red" disabled={loading}>
                    Cancel
                </Button>
                <Button onClick={installPlugin} color="button_green" disabled={loading} autoFocus>
                    OK
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default ConfirmPluginInstallationDialogue;