/**
 * File: DeviceItem.jsx
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
import {ListItem, ListItemText, ListItemIcon, IconButton, CardContent, Card, Tooltip} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import apIcon from '../../images/wifi.png';
import switchIcon from '../../images/hub.png';
import serverIcon from '../../images/server.png';
import SettingsIcon from '@mui/icons-material/Settings';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';

function DeviceItem({ device, onDelete, onEdit, onViewDetails, onNuke}) {
    const deviceIcons = {
        'access_point': apIcon,
        'switch': switchIcon,
        'server': serverIcon,
    };
    const deviceIcon = deviceIcons[device.device_type]

    return (
        <Card sx={{
            margin: 2,
            maxWidth: 600,
            bgcolor: '#02032F',
            boxShadow: 3,
        }}>
            <CardContent>
                <ListItem>
                    <ListItemIcon  sx={{
                        padding: 2,
                    }}>
                        <img src={deviceIcon} alt={device.device_type} style={{ width: '48px', height: '48px' }} />
                    </ListItemIcon>
                    <ListItemText primary={device.name} secondary={device.lan_ip_address} sx={{paddingLeft: 4, paddingRight: 4}}/>
                    <Tooltip title="Device Overview and Settings">
                        <IconButton edge="end" onClick={() => onViewDetails(device.lan_ip_address)} aria-label="view details" sx={{
                            color: '#b1b1e1',
                            padding: 1,
                        }}>
                            <SettingsIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title='Edit Basic Device Details'>
                    <IconButton edge="end" onClick={() => onEdit(device)} aria-label="edit" sx={{
                        color: '#b1b1e1',
                        padding: 1,
                    }}>
                        <EditIcon />
                    </IconButton>
                    </Tooltip>

                    {/*<Tooltip title=''>*/}
                    {/*<IconButton edge="end" onClick={() => onEditPorts(device)} aria-label="edit" sx={{*/}
                    {/*    color: '#b1b1e1',*/}
                    {/*    padding: 1,*/}
                    {/*}}>*/}
                    {/*    <LanIcon />*/}
                    {/*</IconButton>*/}
                    {/*</Tooltip>*/}


                    <Tooltip title='Delete this device'>
                    <IconButton edge="end" aria-label="delete"  onClick={() => onDelete(device)} sx={{
                        color: '#bf0000',
                        padding: 1,
                    }} >
                        <DeleteIcon />
                    </IconButton>
                    </Tooltip>

                    <Tooltip title='Nuke this device'>
                        <IconButton edge="end" aria-label="nuke"  onClick={() => onNuke(device)} sx={{
                            color: '#bf0000',
                            padding: 1,
                        }} >
                            <LocalFireDepartmentIcon />
                        </IconButton>
                    </Tooltip>

                </ListItem>
            </CardContent>
        </Card>
    );
}

export default DeviceItem;