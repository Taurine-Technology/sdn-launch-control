import React from 'react';
import { Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Button } from '@mui/material';

function ConfirmDeleteDialog({ open, handleClose, handleConfirm }) {
    return (
        <Dialog
            open={open}
            onClose={handleClose}
        >
            <DialogTitle>{"Confirm Deletion"}</DialogTitle>
            <DialogContent>
                <DialogContentText>
                    Are you sure you want to delete this device? This action is permanent.
                </DialogContentText>
            </DialogContent>
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