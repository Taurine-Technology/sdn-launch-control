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

const PluginItem = ({ plugin, onDelete, onInstall }) => {
    const [openInfo, setOpenInfo] = useState(false);
    const [openConfirmDialogue, setOpenConfirmDialogue] = useState(false);
    const [installed, setInstalled] = useState(false);
    const [responseMessage, setResponseMessage] = useState('');
    const [responseType, setResponseType] = useState('');

    useEffect(() => {
        const checkPluginInstallation = async () => {
            try {
                // Adjust the URL and payload as needed to match your API endpoint for checking the plugin status
                const response = await axios.get('http://localhost:8000/plugins/check/tau-traffic-classification-sniffer/');
                setInstalled(response.data.hasDevices);
            } catch (error) {
                console.error('Error checking plugin installation:', error);
            } finally {

            }
        };

        checkPluginInstallation();
    }, []);


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
                    {plugin.installed === "yes" ? (
                        <Tooltip title="Delete Plugin">
                            <IconButton color="error" onClick={() => onDelete(plugin)}>
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
                    installed={installed}
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
