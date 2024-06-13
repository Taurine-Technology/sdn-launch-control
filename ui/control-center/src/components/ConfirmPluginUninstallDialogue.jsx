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

function ConfirmPluginUninstallDialogue({ open, handleClose, itemName = "item", isLoading, pluginName}) {
    const [loading, setLoading] = useState(false);
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState(''); // 'success' or 'error'

    const uninstallPlugin = async () => {
        setLoading(true);

        try {
            const response = await axios.post(`http://localhost:8000/plugins/uninstall/${pluginName}/`);
            setResponseType('success')
            setResponseMessage(`Successfully uninstalled ${itemName}`)
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
            <DialogTitle>{"Confirm Plugin Uninstall"}</DialogTitle>
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
                <Button onClick={uninstallPlugin} color="button_green" disabled={loading} autoFocus>
                    OK
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default ConfirmPluginUninstallDialogue;