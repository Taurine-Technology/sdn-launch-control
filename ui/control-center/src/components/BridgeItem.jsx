import React from 'react';
import { Card, CardContent, ListItem, ListItemText, ListItemIcon, IconButton, Tooltip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import bridgeIcon from '../images/bridge.png';

const BridgeItem = ({ bridge, onEdit, onDelete }) => {
    console.log(bridge);

    return (
        <Card sx={{ margin: 2, maxWidth: 600, bgcolor: '#7456FD', boxShadow: 3 }}>
            <CardContent>
                <ListItem>
                    <ListItemIcon sx={{ padding: 2 }}>
                        <img src={bridgeIcon} alt="bridge_icon" style={{ width: '48px', height: '48px' }} />
                    </ListItemIcon>
                    <ListItemText primary={`${bridge.name}`} sx={{paddingLeft: 2, paddingRight: 2}}/>

                    <Tooltip title="Edit Bridge">
                        <IconButton edge="end" onClick={() => onEdit(bridge)} aria-label="edit" sx={{ color: '#3a3939', padding: 1 }}>
                            <EditIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Bridge">
                        <IconButton edge="end" aria-label="delete" onClick={() => onDelete(bridge)} sx={{ padding: 1 }}>
                            <DeleteIcon color="error" />
                        </IconButton>
                    </Tooltip>

                </ListItem>
                <ListItemText secondary={`DPID: ${bridge.dpid}`} sx={{paddingLeft: 4, paddingRight: 4}}/>
                <ListItemText secondary={`Ports: ${bridge.ports.map(port => port.name).join(', ')}`} sx={{paddingLeft:4, paddingRight:4}} />
                {bridge.controller && (
                    <div>
                <ListItemText secondary={`Controller Type: ${bridge.controller.type}`} sx={{paddingLeft:4, paddingRight:4}} />
                <ListItemText secondary={`Controller IP: ${bridge.controller.lan_ip_address}`} sx={{paddingLeft:4, paddingRight:4}} />
                    </div>
            )}

            </CardContent>
        </Card>
    );
};

export default BridgeItem;
