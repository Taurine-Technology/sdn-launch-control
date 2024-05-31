import React from 'react';
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

function NukeDeviceDialogue({ open, handleClose, handleConfirm, isLoading }) {
    return (
        <Dialog open={open} onClose={handleClose} sx={{ '& .MuiDialog-paper': { minWidth: '600px' }} }>
            <DialogTitle color="#bf0000" >{"WARNING"}</DialogTitle>
            {isLoading ? (
                <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                    <CircularProgress />
                </Box>
            ) : (
                <DialogContentText color='#bf0000' sx={{paddingLeft:3}}>
                    Are you sure you want to nuke this device? This action is permanent and does not change
                    device settings, it only edits the Launch Control's database.
                </DialogContentText>
            )}
            <DialogActions>
                <Button onClick={handleClose} color="button_green" disabled={isLoading}>
                    Cancel
                </Button>
                <Button onClick={handleConfirm} color="button_red" disabled={isLoading} autoFocus>
                    OK
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default NukeDeviceDialogue;