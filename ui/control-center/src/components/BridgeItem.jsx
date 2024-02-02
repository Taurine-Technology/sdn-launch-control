import React from 'react';
import { Card, CardContent, ListItem, ListItemText, ListItemIcon, IconButton, Tooltip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import bridgeIcon from '../images/bridge.png'
const BridgeItem = ({ bridge, onEdit, onDelete }) => {
    console.log(bridge);
    return (

        <Card sx={{ margin: 2, maxWidth: 600, bgcolor: '#7456FD', boxShadow: 3 }}>
            <CardContent>
                <ListItem>
                    <ListItemIcon>
                        <ListItemIcon  sx={{
                            padding: 2,
                        }}>
                            <img src={bridgeIcon} alt='bridge_icon' style={{ width: '48px', height: '48px' }} />
                        </ListItemIcon>
                    </ListItemIcon>
                    <ListItemText primary={`${bridge.name} on ${bridge.device?.name || 'Unknown device'}`} secondary={`DPID: ${bridge.dpid}`} />

                    <Tooltip title='Edit Bridge'>
                        <IconButton edge="end" onClick={() => onEdit(bridge)} aria-label="edit" sx={{
                            color: '#3a3939',
                            padding: 1,
                        }}>
                            <EditIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Bridge">
                        <IconButton edge="end" aria-label="delete" onClick={() => onDelete(bridge)}>
                            <DeleteIcon color="error" />
                        </IconButton>
                    </Tooltip>
                </ListItem>
            </CardContent>
        </Card>
    );
};

export default BridgeItem;
