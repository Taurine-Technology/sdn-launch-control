/**
 * File: ClassificationGraph.jsx
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

import React, { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import {Card, CardContent, Typography} from '@mui/material';
import Box from "@mui/material/Box";

function ClassificationGraph() {
    const [classificationData, setClassificationData] = useState([]);
    const classificationDataRef = useRef(classificationData);

    useEffect(() => {
        const flowSocket = new WebSocket('ws://127.0.0.1:8000/ws/flow_updates/');

        flowSocket.onmessage = function(event) {
            console.log('Received data:', event.data);
            const data = JSON.parse(event.data);
            if (data.flow) { // data.flow is expected to be the classification string directly
                const categoryName = findCategory(data.flow); // Use data.flow directly
                updateClassificationData(categoryName);
            } else {
                console.error('Invalid or missing flow data', data);
            }
        };




        return () => {
            flowSocket.close();
        };
    }, []);

    const findCategory = (service) => {
        const categoryMapping = {
            'Networking': ['CLOUDFLARE', 'HTTP', 'TLS', 'CYBERSEC'],
            'Social Media': ['FACEBOOK', 'INSTAGRAM', 'SNAPCHAT', 'TIKTOK', 'TWITTER'],
            'Chat': ['WHATSAPPFILES', 'WHATSAPP'],
            'Google Services': ['GMAIL', 'GOOGLECLOUD', 'GOOGLEDOCS', 'GOOGLESERVICES', 'GOOGLE'],
            'Streaming': ['YOUTUBE'],
            'Android Services': ['XIAOMI'],
            'iPhone Services': ['APPLE'],
            'Music Streaming': ['SPOTIFY']
        };
        for (const [category, services] of Object.entries(categoryMapping)) {
            if (services.includes(service.toUpperCase())) {
                return category;
            }
        }
        return service; // Default to the service name if no category match
    };

    const updateClassificationData = (categoryName) => {
        let newClassificationData = [...classificationDataRef.current];
        const index = newClassificationData.findIndex(data => data.name === categoryName);

        if (index !== -1) {
            newClassificationData[index].value += 1;
        } else {
            newClassificationData.push({ name: categoryName, value: 1 });
        }

        setClassificationData(newClassificationData);
        classificationDataRef.current = newClassificationData;
    };

    return (
        <Card raised sx={{ margin: 4, bgcolor: '#02032F', boxShadow: 3}}>
            <CardContent>
                <Typography variant="h2" sx={{ mb: 2, color: "#FFF" }}>Flow Traffic Classifications</Typography>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400, width: '100%' }}>
                    <BarChart
                        data={classificationData}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                        width={1000} height={400}

                    >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis label={{ value: 'Number of Flows', angle: -90, position: 'insideLeft' }}/>
                        <Tooltip />
                        <Bar dataKey="value" fill="#8884d8" />
                    </BarChart>
                </Box>
        </CardContent>
</Card>
    );
}

export default ClassificationGraph;
