import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, Typography, Box, Alert, CircularProgress, } from "@mui/material";
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import switchIcon from '../images/hub.png';
import serverIcon from '../images/server.png';
const OvsNetworkDiagram = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [alert, setAlert] = useState({ show: false, type: '', message: '' });
    const d3Container = useRef(null);
    const [apiCallSuccess, setApiCallSuccess] = useState(true);
    const [selectedNode, setSelectedNode] = useState({
        id: '',
        type: '',
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
        setIsLoading(true)
        fetch('http://localhost:8000/ovs-network-map/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                setIsLoading(false);
                setApiCallSuccess(true);
                if (d3Container.current) {

                    const nodes = [];
                    const links = [];

                    // Process each switch and its flows to create nodes and links
                    Object.entries(data.data).forEach(([switchName, switchInfo]) => {
                        switchInfo.bridges.forEach(bridge => {

                            const switchNode = {
                                id: bridge.name,
                                type: 'switch',
                                controller: bridge.controller_name,
                            };
                            nodes.push(switchNode);

                            // Process flows to create device nodes and links
                            bridge.flows?.forEach(flow => {
                                const sourceDevice = {
                                    id: flow.dl_src,
                                    type: 'device',
                                };
                                const targetDevice = {
                                    id: flow.dl_dst,
                                    type: 'device',
                                };

                                // Add devices if they don't exist
                                if (!nodes.find(node => node.id === sourceDevice.id)) {
                                    nodes.push(sourceDevice);
                                }
                                if (!nodes.find(node => node.id === targetDevice.id)) {
                                    nodes.push(targetDevice);
                                }

                                // Create links between devices and the switch
                                links.push({ source: flow.dl_src, target: bridge.name });
                                links.push({ source: flow.dl_dst, target: bridge.name });
                            });

                            // Link switch to controller if not already linked
                            if (!links.find(link => link.source === bridge.controller_name)) {
                                const controllerNode = {
                                    id: bridge.controller_name,
                                    type: 'controller',
                                };
                                if (!nodes.find(node => node.id === controllerNode.id)) {
                                    nodes.push(controllerNode);
                                }
                                links.push({ source: bridge.name, target: bridge.controller_name });
                            }
                        });
                    });

                    drawDiagram(d3Container.current, links, nodes);

                }


            })
            .catch(error => {
                console.error('Fetch error:', error);
                setApiCallSuccess(false);
                setIsLoading(false);
            });

    }, []);

    const drawDiagram = (container, links, nodes) => {

        const svg = d3.select(container);
        if (!svg) {
            console.log('SVG not found');
            return;
        }
        svg.selectAll("*").remove(); // Clear SVG content before redrawing

        svg.attr('width', dimensions.width).attr('height', dimensions.height);

        const iconSize = 40;
        const iconOffset = iconSize / 2; // Offset to center the icon


        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100)) // link distance
            .force("charge", d3.forceManyBody())
            .force("center", d3.forceCenter(dimensions.width / 2, dimensions.height / 2))
            .force("collide", d3.forceCollide().radius(50)); // radius for collision detection


        // Draw lines for the links
        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke-width", 5)
            .attr("stroke", "#7456FD");

        // Conditional node rendering
        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("node")
            .data(nodes)
            .enter()
            .append(d => {
                // Create a document fragment to conditionally append different elements
                const docFrag = document.createDocumentFragment();
                if (d.type === 'switch' || d.type === 'controller') {
                    const image = document.createElementNS("http://www.w3.org/2000/svg", "image");
                    image.setAttributeNS(null, 'href', d.type === 'switch' ? switchIcon : serverIcon);
                    image.setAttributeNS(null, 'width', 40);
                    image.setAttributeNS(null, 'height', 40);
                    return docFrag.appendChild(image);
                } else {
                    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                    circle.setAttributeNS(null, 'r', 10);
                    circle.setAttributeNS(null, 'fill', '#3D019F');
                    return docFrag.appendChild(circle);
                }
            })
            .attr("transform", d => `translate(${d.type === 'device' ? -10 : -20}, ${d.type === 'device' ? -10 : -20})`)
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
            link.attr("x1", d => d.source.x + (d.source.type === 'switch' || d.source.type === 'controller' ? iconOffset : 0))
                .attr("y1", d => d.source.y + (d.source.type === 'switch' || d.source.type === 'controller' ? iconOffset : 0))
                .attr("x2", d => d.target.x + (d.target.type === 'switch' || d.target.type === 'controller' ? iconOffset : 0))
                .attr("y2", d => d.target.y + (d.target.type === 'switch' || d.target.type === 'controller' ? iconOffset : 0));

            node.attr("transform", d => `translate(${d.x}, ${d.y})`);
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
            <Card sx={{ margin: 2, bgcolor: '#02032F', boxShadow: 3 }}>
                <CardContent>
                    {isLoading && (
                        <Box sx={{
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            paddingTop: '10px',
                            height: '100%',
                        }}>
                            <CircularProgress size={100}/>
                        </Box>
                    )}
                    <div>

                        {apiCallSuccess ? (
                                    <svg ref={d3Container}></svg>
                                ) : (
                                    <Box sx={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        height: '100%',
                                        padding: 4
                                    }}>
                                        <ErrorOutlineIcon sx={{fontSize: 60, color: '#7456FD', padding: "20px"}}/>
                                        <Typography variant="body">
                                            Unable to load the network diagram. Check your connection and try again.
                                        </Typography>
                                    </Box>
                                )
                            }
                        {selectedNode && (
                            <Card sx={{maxWidth: 345, margin: 2, bgcolor: '#7456FD'}}>
                        <CardContent>
                            <Typography gutterBottom variant="h2">
                                Details
                            </Typography>
                            <Typography variant="body">
                                ID: {selectedNode.id}<br/>
                                Type: {selectedNode.type}<br/>
                            </Typography>
                        </CardContent>
            </Card>
                        )}
                    )
                </div>
            </CardContent>
        </Card>

    );
};

export default OvsNetworkDiagram;
