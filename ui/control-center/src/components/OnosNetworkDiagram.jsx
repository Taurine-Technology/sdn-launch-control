import React, {useEffect, useRef, useState} from 'react';
import * as d3 from 'd3';
import {Card, CardContent, Typography, Box} from "@mui/material";
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

const OnosNetworkDiagram = () => {
    const d3Container = useRef(null);
    const [apiCallSuccess, setApiCallSuccess] = useState(true);
    const [selectedNode, setSelectedNode] = useState({
        id: '',
        role: '',
        driver: '',
        softwareVersion: '',
        protocol: '',
        managementAddress: ''
    });
    const [dimensions, setDimensions] = useState({
        width: window.innerWidth * 0.8,
        height: window.innerHeight * 0.5,
    });
    useEffect(() => {
        const handleResize = () => {
            setDimensions({
                width: window.innerWidth * 0.8,
                height: window.innerHeight * 0.5,
            });
        };

        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);
    }, []);
    useEffect(() => {
        fetch('http://localhost:8000/onos-network-map/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log(data);
                if (d3Container.current) {
                    // Transforming links for D3
                    const links = data.links.map(link => ({
                        source: link.src.device,
                        target: link.dst.device,
                    }));

                    // Extracting unique device IDs to create nodes from links
                    const devices = new Set(links.flatMap(link => [link.source, link.target]));

                    // Add devices from clusters with linkCount of 0 that are not already in the devices set
                    data.clusters.forEach(cluster => {
                        if (cluster.linkCount === 0 && !devices.has(cluster.root)) {
                            devices.add(cluster.root);
                        }
                    });
                    const nodes = Array.from(devices).map(device => {
                        // Find the matching device info
                        const deviceInfo = data.device_info.find(d => d.id === device);
                        return {
                            id: device,
                            role: deviceInfo?.role ?? 'Unknown',
                            driver: deviceInfo?.driver ?? 'Unknown',
                            softwareVersion: deviceInfo?.sw ?? 'Unknown',
                            protocol: deviceInfo?.annotations?.protocol ?? 'Unknown',
                            managementAddress: deviceInfo?.annotations?.managementAddress ?? 'Unknown',
                        };
                    });

                    console.log(nodes);

                    drawDiagram(d3Container.current, links, nodes);
                }
                setApiCallSuccess(true);
            })
            .catch(error => {
                console.error('Fetch error:', error);
                setApiCallSuccess(false);
            });
    }, [dimensions]);

    const drawDiagram = (container, links, nodes) => {
        const svg = d3.select(container);
        svg.selectAll("*").remove(); // Clear SVG content before redrawing

        svg.attr('width', dimensions.width).attr('height', dimensions.height);

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id))
            .force("charge", d3.forceManyBody())
            .force("center", d3.forceCenter(dimensions.width / 2, dimensions.height / 2));

        // Draw lines for the links
        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke-width", 5)
            .attr("stroke", "#7456FD");

        // Draw circles for the nodes
        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("r", 10)
            .attr("fill", "#3D019F")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("click", (event, d) => {

                setSelectedNode(d);
            });

        node.append("title")
            .text(d => d.id);

        // Update force simulation on tick
        simulation.on("tick", () => {
            link.attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("cx", d => d.x)
                .attr("cy", d => d.y);
        });

        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
    };

    return (
        <Card sx={{
            margin: 2,
            // maxWidth: 600,
            bgcolor: '#02032F',
            boxShadow: 3,
        }}>
            {apiCallSuccess ? (
                <svg ref={d3Container}></svg>

            ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 4 }}>
                    <ErrorOutlineIcon sx={{ fontSize: 60, color: '#7456FD', padding: "20px" }} />
                    <Typography variant="body">
                        Unable to load your network diagram. If there are no compatible devices connected then ignore or check your connection and try again.
                    </Typography>
                </Box>
            )}

            {selectedNode && (
                <Card sx={{ maxWidth: 345, margin: 2, bgcolor: '#7456FD'}}>
                    <CardContent>
                        <Typography gutterBottom variant="h2">
                            Device Details
                        </Typography>
                        <Typography variant="body">
                            ID: {selectedNode.id}<br />
                            Role: {selectedNode.role}<br />
                            Driver: {selectedNode.driver}<br />
                            Software Version: {selectedNode.softwareVersion}<br />
                            Protocol: {selectedNode.protocol}<br />
                            Management Address: {selectedNode.managementAddress}
                        </Typography>
                    </CardContent>
                </Card>
            )}
        </Card>
    );
};

export default OnosNetworkDiagram;
