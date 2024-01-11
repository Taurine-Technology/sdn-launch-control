import React from 'react';
import {ListItem, ListItemText, ListItemIcon, IconButton, CardContent, Card} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import apIcon from '../images/wifi.png';
import switchIcon from '../images/hub.png';

function DeviceItem({ device, onDelete, onEdit}) {
    const deviceIcon = device.device_type === 'access_point' ? apIcon : switchIcon;

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
                    <IconButton edge="end" onClick={() => onEdit(device)} aria-label="edit" sx={{
                        color: '#b1b1e1',
                        padding: 1,
                    }}>
                        <EditIcon />
                    </IconButton>
                    <IconButton edge="end" aria-label="delete"  onClick={() => onDelete(device)} sx={{
                        color: '#bf0000',
                        padding: 2,
                    }} >
                        <DeleteIcon />
                    </IconButton>
                </ListItem>
            </CardContent>
        </Card>
    );
}

export default DeviceItem;