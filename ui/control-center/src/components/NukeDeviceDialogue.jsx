/**
 * File: NukeDeviceDialogue.jsx
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