/**
 * File: ConfirmPluginInstallationDialogue.jsx
 * Copyright (C) 2025 Keegan White
 *
 * This file is part of the SDN Launch Control project.
 *
 * This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
 * available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
 *
 * Contributions to this project are governed by a Contributor License Agreement (CLA).
 * By submitting a contribution, contributors grant Keegan White exclusive rights to
 * the contribution, including the right to relicense it under a different license
 * at the copyright owner's discretion.
 *
 * Unless required by applicable law or agreed to in writing, software distributed
 * under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the GNU General Public License for more details.
 *
 * For inquiries, contact Keegan White at keeganwhite@taurinetech.com.
 */

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

        if (pluginName === 'tau-onos-metre-traffic-classification' && !installed) {
            setResponseType('error');
            setResponseMessage('Please install the Traffic Classification Sniffer to enable this plugin.');
            setLoading(false);
            return;  // Early exit if the condition is not met
        }

        try {
            const response = await axios.post(`http://localhost:8000/plugins/install/${pluginName}/`);
            setResponseType('success')
            setResponseMessage(`Successfully installed ${itemName}`)
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