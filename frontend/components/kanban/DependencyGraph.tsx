/**
 * Dependency Graph Visualization Component (Stream F Enhancement)
 * 
 * Visualizes task dependencies as a directed graph
 */
'use client';

import React, { useEffect, useState, useRef } from 'react';
import { apiClient } from '@/lib/api';

interface DependencyNode {
  id: string;
  title: string;
  phase: string;
  status: string;
  label: string;
}

interface DependencyEdge {
  from: string;
  to: string;
  type: string;
  label: string;
}

interface DependencyGraphData {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  execution_id: string;
  total_tasks: number;
  total_dependencies: number;
}

interface DependencyGraphProps {
  executionId: string;
  onNodeClick?: (nodeId: string) => void;
}

export function DependencyGraph({ executionId, onNodeClick }: DependencyGraphProps) {
  const [graphData, setGraphData] = useState<DependencyGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    loadGraphData();
  }, [executionId]);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getDependencyGraph(executionId);
      setGraphData(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dependency graph');
      console.error('Error loading dependency graph:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'investigation':
        return '#a855f7'; // Purple
      case 'building':
        return '#3b82f6'; // Blue
      case 'validation':
        return '#10b981'; // Green
      default:
        return '#6b7280'; // Gray
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10b981'; // Green
      case 'in_progress':
        return '#3b82f6'; // Blue
      case 'pending':
        return '#fbbf24'; // Yellow
      case 'blocked':
        return '#ef4444'; // Red
      default:
        return '#6b7280'; // Gray
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 border rounded-lg">
        <div className="text-gray-500">Loading dependency graph...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 border rounded-lg bg-red-50">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 border rounded-lg bg-gray-50">
        <div className="text-gray-500">No tasks to visualize</div>
      </div>
    );
  }

  // Simple force-directed layout simulation
  const width = 800;
  const height = 600;
  const nodeRadius = 25;
  const nodePositions: Map<string, { x: number; y: number }> = new Map();

  // Simple grid layout
  const cols = Math.ceil(Math.sqrt(graphData.nodes.length));
  const rows = Math.ceil(graphData.nodes.length / cols);
  const spacingX = width / (cols + 1);
  const spacingY = height / (rows + 1);

  graphData.nodes.forEach((node, index) => {
    const col = index % cols;
    const row = Math.floor(index / cols);
    nodePositions.set(node.id, {
      x: spacingX * (col + 1),
      y: spacingY * (row + 1),
    });
  });

  return (
    <div className="w-full">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Task Dependencies</h3>
        <div className="text-sm text-gray-600">
          {graphData.total_tasks} tasks • {graphData.total_dependencies} dependencies
        </div>
      </div>

      <div className="border rounded-lg bg-white p-4 overflow-auto">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto"
        >
          {/* Draw edges */}
          {graphData.edges.map((edge, index) => {
            const fromNode = nodePositions.get(edge.from);
            const toNode = nodePositions.get(edge.to);
            
            if (!fromNode || !toNode) return null;

            return (
              <line
                key={`edge-${index}`}
                x1={fromNode.x}
                y1={fromNode.y}
                x2={toNode.x}
                y2={toNode.y}
                stroke="#94a3b8"
                strokeWidth="2"
                markerEnd="url(#arrowhead)"
                className="opacity-60"
              />
            );
          })}

          {/* Arrow marker definition */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#94a3b8" />
            </marker>
          </defs>

          {/* Draw nodes */}
          {graphData.nodes.map((node) => {
            const position = nodePositions.get(node.id);
            if (!position) return null;

            const phaseColor = getPhaseColor(node.phase);
            const statusColor = getStatusColor(node.status);

            return (
              <g key={node.id}>
                <circle
                  cx={position.x}
                  cy={position.y}
                  r={nodeRadius}
                  fill={phaseColor}
                  fillOpacity={0.2}
                  stroke={phaseColor}
                  strokeWidth="2"
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => onNodeClick?.(node.id)}
                />
                <circle
                  cx={position.x}
                  cy={position.y}
                  r={nodeRadius * 0.6}
                  fill={statusColor}
                  fillOpacity={0.8}
                />
                <text
                  x={position.x}
                  y={position.y + nodeRadius + 15}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#374151"
                  className="pointer-events-none"
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-purple-200 border border-purple-500"></div>
          <span>Investigation</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-blue-200 border border-blue-500"></div>
          <span>Building</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-200 border border-green-500"></div>
          <span>Validation</span>
        </div>
      </div>
    </div>
  );
}

