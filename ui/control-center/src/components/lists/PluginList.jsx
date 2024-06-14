import React from 'react';
import { List } from '@mui/material';
import PluginItem from "../items/PluginItem";

const PluginList = ({ plugins, onDelete, onInstall, fetchPlugins }) => {
    return (
        <List>
            {plugins.map((plugin, index) => (
                <PluginItem
                    key={index}
                    plugin={plugin}
                    onDelete={onDelete}
                    onInstall={onInstall}
                    fetchPlugins={fetchPlugins}
                />
            ))}
        </List>
    );
};

export default PluginList;
