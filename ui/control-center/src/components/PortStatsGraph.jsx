import React, {useEffect, useRef, useState} from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, CardContent } from "@mui/material";
import Box from "@mui/material/Box";

const PortStatsGraph = ({ targetIpAddress, targetPorts}) => {
    const [data, setData] = useState([]);
    const wsUrl = "ws://localhost:8000/ws/openflow_metrics/";  // Update to match your WebSocket URL
    const portColors = useRef({});
    useEffect(() => {
        // Generate a unique color for each port in targetPorts
        targetPorts.forEach(portObj => {
            const port = portObj.name;
            portColors.current[port] = `#${Math.floor(Math.random() * 16777215).toString(16)}`;
        });

        console.log('PORTS', targetPorts)
        const ws = new WebSocket(wsUrl);
        ws.onmessage = (event) => {
            const stats = JSON.parse(event.data);
            console.log("WebSocket message received:", stats);
            if (stats.message.ip_address === targetIpAddress) {
                const portsData = stats.message.ports;
                const targetPortNames = targetPorts.map(p => p.name); // Extract the names into an array
                const filteredPorts = Object.keys(portsData)
                    .filter(key => targetPortNames.includes(key)) // Use the array for filtering
                    .reduce((obj, key) => {
                        obj[key] = portsData[key];
                        return obj;
                    }, {});

                const newData = {
                    time: new Date().toISOString().substr(11, 8), // Convert ISO string to HH:MM:SS
                    ...filteredPorts
                };
                console.log("Processed newData:", newData);
                setData(currentData => {
                    const newDataArray = [...currentData, newData];
                    const sixtySecondsAgo = new Date(new Date().getTime() - 60000).toISOString().substr(11, 8);
                    return newDataArray.filter(item => item.time >= sixtySecondsAgo);
                });
            }
        };

        return () => {
            ws.close();
        };
    }, [wsUrl, targetIpAddress, targetPorts]);

    return (
        <Card raised sx={{bgcolor: '#02032F',  margin: 4, }}>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300, width: '100%' }}>
                    {data.length > 0 ? (

                            <LineChart width={700} height={400} data={data}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis domain={['auto', 'auto']} label={{ value: 'Throughput (Mbps)', angle: -90, position: 'insideLeft' }} />
                                <Tooltip formatter={(value) => `${value.toFixed(2)} Mbps`} />
                                <Legend verticalAlign="bottom" height={36}/>
                                {targetPorts.map((portObj, idx) => (
                                    data[0][portObj.name] !== undefined && (
                                        <Line key={idx} type="monotone" dataKey={portObj.name} stroke={portColors.current[portObj.name]} name={`Port ${portObj.name} Throughput`} activeDot={{ r: 8 }} />
                                    )
                                ))}
                            </LineChart>

                    ) : <div style={{ color: '#fff' }}>No data available</div>}
                </Box>
            </CardContent>
        </Card>
    );
};

export default PortStatsGraph;
