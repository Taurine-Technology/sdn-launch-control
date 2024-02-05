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
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>{"Confirm Deletion"}</DialogTitle>
            {isLoading ? (
                <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                    <CircularProgress />
                </Box>
            ) : (
                <DialogContentText>
                    Are you sure you want to delete this {itemName}? This action is permanent.
                </DialogContentText>
            )}
            <DialogActions>
                <Button onClick={handleClose} color="button_green">
                    Cancel
                </Button>
                <Button onClick={handleConfirm} color="button_red" autoFocus>
                    OK
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default ConfirmDeleteDialog;