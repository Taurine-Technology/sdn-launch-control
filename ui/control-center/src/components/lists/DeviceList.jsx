import React from 'react';
import DeviceItem from '../items/DeviceItem';
import {Grid, List} from '@mui/material';

function DeviceList({ devices, onDelete,  onEdit, onNuke, onViewDetails}) {
    return (
        <List>
            <Grid container>
                <Grid item>
                    {devices.map(device => (
                        <DeviceItem key={device.lan_ip_address} device={device} onNuke={onNuke} onDelete={onDelete} onEdit={onEdit} onViewDetails={onViewDetails} />
                    ))}
                </Grid>

            </Grid>
        </List>
    );
}

export default DeviceList;