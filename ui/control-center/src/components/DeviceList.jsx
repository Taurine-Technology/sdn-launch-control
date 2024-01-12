import React from 'react';
import DeviceItem from './DeviceItem';
import {Grid, List} from '@mui/material';

function DeviceList({ devices, onDelete,  onEdit, onViewDetails}) {
    return (
        <List>
            <Grid container>
                <Grid item>
                    {devices.map(device => (
                        <DeviceItem key={device.lan_ip_address} device={device} onDelete={onDelete} onEdit={onEdit} onViewDetails={onViewDetails} />
                    ))}
                </Grid>

            </Grid>
        </List>
    );
}

export default DeviceList;