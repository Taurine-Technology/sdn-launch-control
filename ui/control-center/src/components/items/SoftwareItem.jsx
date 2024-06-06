import React, { useState } from 'react';
import {
    ListItem,
    Paper,
    Typography,
    Box,
    IconButton,
    Tooltip,
    DialogTitle,
    DialogContentText,
    DialogContent, Dialog, Button, DialogActions
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import DownloadIcon from '@mui/icons-material/Download';
import InstallFormDialogue from "../InstallFormDialogue";

const SoftwareItem = ({ software }) => {
    const [openInfo, setOpenInfo] = useState(false);
    const [openInstallDialog, setOpenInstallDialog] = useState(false);

    const handleOpenInfo = () => {
        setOpenInfo(true);
    };
    const [openDialog, setOpenDialog] = useState(false);

    const handleCloseInfo = () => {
        setOpenInfo(false);
    };

    const handleOpenInstallDialog = () => {
        setOpenInstallDialog(true);
    };

    const handleCloseInstallDialog = () => {
        setOpenInstallDialog(false);
    };
    const handleOpenDialog = () => {
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
    };

    return (
        <ListItem sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Paper elevation={3} sx={{ width: '100%', p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: "#02032F", color: "#fff" }}>
                <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">{software.title}</Typography>
                    <Typography variant="body2">{software.shortDescription}</Typography>
                </Box>
                <Box>
                    <Tooltip title="View Information">
                        <IconButton color="info" onClick={handleOpenDialog}>
                            <InfoIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Install Software">
                        <InstallFormDialogue
                            installationType={software.title}
                            endpoint={software.endpoint}
                            open={openInstallDialog}
                            onClose={handleCloseInstallDialog}
                        />
                    </Tooltip>
                </Box>
            </Paper>
            <Dialog open={openDialog} onClose={handleCloseDialog}>
                <DialogTitle>{software.title}</DialogTitle>
                <DialogContent>
                    <DialogContentText>{software.longDescription}</DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>Close</Button>
                </DialogActions>
            </Dialog>

        </ListItem>
    );
};

export default SoftwareItem;
