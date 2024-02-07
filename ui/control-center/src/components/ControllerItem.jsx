
import React from 'react';
import {Card, CardContent, ListItem, ListItemText, ListItemIcon, Tooltip, IconButton} from '@mui/material';
import controllerIcon from '../images/controller.png';
import SettingsIcon from "@mui/icons-material/Settings";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
function ControllerItem({ controller }) {
    console.log(`${controller.switches}`)
    return (
        <Card sx={{ margin: 2, bgcolor: '#02032F', boxShadow: 3, }}>
            <CardContent>
                <ListItem>
                    <ListItemIcon  sx={{
                        padding: 2,
                    }}>
                        <img src={controllerIcon} alt='controller icon' style={{ width: '48px', height: '48px' }} />
                    </ListItemIcon>
                    <ListItemText primary={`${controller.type}`} secondary={`${controller.lan_ip_address}`} sx={{paddingLeft: 4, paddingRight: 4}} />
                    <Tooltip title="Contorller Overview and Settings">
                        <IconButton edge="end" onClick={() => console.log('clicked overview')} aria-label="view details" sx={{
                            color: '#b1b1e1',
                            padding: 1,
                        }}>
                            <SettingsIcon />
                        </IconButton>
                    </Tooltip>

                    <Tooltip title='Edit Basic Device Details'>
                        <IconButton edge="end" onClick={() => console.log('clicked edit')} aria-label="edit" sx={{
                            color: '#b1b1e1',
                            padding: 1,
                        }}>
                            <EditIcon />
                        </IconButton>
                    </Tooltip>

                    <Tooltip title='Delete this controller'>
                    <IconButton edge="end" aria-label="delete"  onClick={() => console.log('clicked delete')} sx={{
                        color: '#bf0000',
                        padding: 1,
                    }} >
                        <DeleteIcon />
                    </IconButton>
                </Tooltip>
                </ListItem>
            </CardContent>
        </Card>
    );
}

export default ControllerItem;
