import React, {useState} from 'react';
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
    DialogContentText, DialogActions, Button
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';

const PluginItem = ({ plugin, onDelete, onInstall }) => {
    const [openInfo, setOpenInfo] = useState(false);

    const handleOpenInfo = () => {
        setOpenInfo(true);
    };

    const handleCloseInfo = () => {
        setOpenInfo(false);
    };
    return (
        <ListItem sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
                    ) : (
                        <Tooltip title="Install Plugin">
                            <IconButton sx={{color: '#b1b1e1',}} onClick={() => onInstall(plugin)}>
                                <DownloadIcon />
                            </IconButton>
                        </Tooltip>
                    )}
                </Box>
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
