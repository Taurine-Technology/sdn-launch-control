/**
 * File: PlugItem.jsx
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

import React, {useEffect, useState} from 'react';
import {
    ListItem,
    Paper,
    Typography,
    Box,
    IconButton,
    Tooltip,
    DialogContent,
    DialogTitle,
    Dialog,
    DialogContentText, DialogActions, Button, Alert
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import InstallSnifferForm from "../installation-plugins/InstallSnifferForm";
import ConfirmPluginInstallationDialogue from "../ConfirmPluginInstallationDialogue";
import axios from "axios";
import ConfirmPluginUninstallDialogue from "../ConfirmPluginUninstallDialogue";

const PluginItem = ({ plugin, onDelete, onInstall, fetchPlugins }) => {
    const [openInfo, setOpenInfo] = useState(false);
    const [openConfirmDialogue, setOpenConfirmDialogue] = useState(false);
    const [openUninstallConfirmDialogue, setOpenUninstallConfirmDialogue] = useState(false);

    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState('');
    const [canInstall, setCanInstall] = useState(false);

    useEffect(() => {


        checkPluginInstallation();
    }, []);
    const checkPluginInstallation = async () => {

        try {
            const pluginStatus = await axios.get(`http://localhost:8000/plugins/check/${plugin.name}/`);
            const controllerResponse = await axios.get('http://localhost:8000/controllers/');
            const hasONOSController = controllerResponse.data.some(controller => controller.type === 'onos');
            setCanInstall(pluginStatus.data && hasONOSController);
        } catch (error) {
            console.error('Error checking plugin and controller status:', error);
            setResponseType('error');
            setResponseMessage('Failed to fetch plugin or controller data.');
        }
    };


    const handleOpenInfo = () => {
        setOpenInfo(true);
    };

    const handleCloseAlert = () => {
        setResponseMessage('')
    }

    const handleCloseInfo = () => {
        setOpenInfo(false);
    };

    const handleCloseConfirm = () => {
        setOpenConfirmDialogue(false);
        fetchPlugins()
    };

    const handleCloseUninstallConfirm = () => {
        setOpenUninstallConfirmDialogue(false);
        fetchPlugins()
    };

    const handleInstallPlugin = () => {

        setOpenConfirmDialogue(true)
    }

    const renderInstallButton = () => {
        if (plugin.name === "tau-traffic-classification-sniffer") {
            return <InstallSnifferForm onInstall={() => onInstall(plugin)} />;
        }

        else {
            return (
                <Tooltip title="Install Plugin">
                    <IconButton sx={{color: '#b1b1e1'}} onClick={handleInstallPlugin}>
                        <DownloadIcon />
                    </IconButton>
                </Tooltip>
            );
        }
    };

    return (
        <ListItem sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {responseMessage && (
                <Alert severity={responseType} onClose={handleCloseAlert}>
                    {responseMessage}
                </Alert>
            )}
            <Paper elevation={3} sx={{ width: '100%', p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: "#02032F", color: "#fff" }}>
                <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">{plugin.alias}</Typography>
                    <Typography variant="body2">Version: {plugin.version}</Typography>
                    <Typography variant="body2">Author: {plugin.author}</Typography>
                    <Typography variant="body1">{plugin.short_description}</Typography>
                </Box>
                <Box>
                    <Tooltip title="View Information">
                        <IconButton color="info" onClick={handleOpenInfo}>
                            <InfoIcon />
                        </IconButton>
                    </Tooltip>
                    {plugin.installed && plugin.name !== 'tau-traffic-classification-sniffer' ? (
                        <Tooltip title="Delete Plugin">
                            <IconButton color="error" onClick={() => setOpenUninstallConfirmDialogue(true)}>
                                <DeleteIcon />
                            </IconButton>
                        </Tooltip>
                    ) : renderInstallButton()}
                </Box>
                <ConfirmPluginInstallationDialogue
                    open={openConfirmDialogue}
                    handleClose={handleCloseConfirm}
                    itemName={plugin.alias}
                    pluginName={plugin.name}
                    isLoading={false}
                    installed={canInstall}
                />
                <ConfirmPluginUninstallDialogue
                    open={openUninstallConfirmDialogue}
                    handleClose={handleCloseUninstallConfirm}
                    itemName={plugin.alias}
                    pluginName={plugin.name}
                    isLoading={false}
                />

            </Paper>
            {/* Info Dialog */}
            <Dialog open={openInfo} onClose={handleCloseInfo} aria-labelledby="plugin-info-title">
                <DialogTitle id="plugin-info-title">{plugin.alias}</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        {plugin.long_description || "No additional information provided."}
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseInfo} color="primary">
                        Close
                    </Button>
                </DialogActions>
            </Dialog>
        </ListItem>
    );
};

export default PluginItem;
