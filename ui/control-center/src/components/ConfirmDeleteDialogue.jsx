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

function ConfirmDeleteDialog({ open, handleClose, handleConfirm, itemName = "item", isLoading }) {
    return (
        <Dialog open={open} onClose={handleClose} sx={{ '& .MuiDialog-paper': { minWidth: '600px' }} }>
            <DialogTitle>{"Confirm Deletion"}</DialogTitle>
            {isLoading ? (
                <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                    <CircularProgress />
                </Box>
            ) : (
                <DialogContentText sx={{paddingLeft:3}}>
                    Are you sure you want to delete this {itemName}? This action is permanent.
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

export default ConfirmDeleteDialog;