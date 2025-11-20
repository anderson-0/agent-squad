'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { squadsAPI } from '@/lib/api/squads';
import { agentsAPI } from '@/lib/api/agents';
import { Squad, Agent } from '@/lib/api/types';
import { DeleteSquadDialog } from '@/components/squads/DeleteSquadDialog';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, Users, Calendar, Edit, Plus } from 'lucide-react';
import { format } from 'date-fns';

export default function SquadDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const squadId = params.id as string;

  const [squad, setSquad] = useState<Squad | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSquadDetails = async () => {
      try {
        setIsLoading(true);
        
        // Fetch squad details
        const squadData = await squadsAPI.getSquad(squadId);
        setSquad(squadData);

        // Fetch squad agents
        const agentsData = await agentsAPI.listAgents(squadId, 1, 100);
        setAgents(agentsData.items);
      } catch (error) {
        console.error('Failed to fetch squad details:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (squadId) {
      fetchSquadDetails();
    }
  }, [squadId]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!squad) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold">Squad not found</h2>
        <p className="text-muted-foreground mt-2">
          The squad you're looking for doesn't exist.
        </p>
        <Link href="/squads">
          <Button className="mt-4">Back to Squads</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/squads">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">{squad.name}</h1>
          {squad.description && (
            <p className="text-muted-foreground mt-1">{squad.description}</p>
          )}
        </div>
        <DeleteSquadDialog squadId={squad.id} squadName={squad.name} />
      </div>

      {/* Squad Info Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>
            {squad.is_active ? (
              <Badge className="bg-green-100 text-green-800">Active</Badge>
            ) : (
              <Badge variant="secondary">Inactive</Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Type</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="secondary">{squad.squad_type}</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Created</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              {format(new Date(squad.created_at), 'MMM d, yyyy')}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Squad Details */}
      <Card>
        <CardHeader>
          <CardTitle>Squad Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Squad ID</span>
              <span className="text-sm text-muted-foreground font-mono">
                {squad.id}
              </span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Organization ID</span>
              <span className="text-sm text-muted-foreground font-mono">
                {squad.organization_id}
              </span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Last Updated</span>
              <span className="text-sm text-muted-foreground">
                {format(new Date(squad.updated_at), 'MMM d, yyyy HH:mm')}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Squad Agents */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Squad Agents</CardTitle>
              <CardDescription>AI agents in this squad</CardDescription>
            </div>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Agent
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {agents.length === 0 ? (
            <div className="text-center py-12">
              <Users className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-semibold">No agents yet</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Add agents to this squad to get started
              </p>
              <Button className="mt-6" size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add First Agent
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Role</TableHead>
                  <TableHead>Specialization</TableHead>
                  <TableHead>LLM Provider</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agents.map((agent) => (
                  <TableRow key={agent.id}>
                    <TableCell className="font-medium">{agent.role}</TableCell>
                    <TableCell>
                      {agent.specialization ? (
                        <Badge variant="secondary">{agent.specialization}</Badge>
                      ) : (
                        <span className="text-muted-foreground">None</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{agent.llm_provider}</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {agent.llm_model}
                    </TableCell>
                    <TableCell>
                      {agent.is_active ? (
                        <Badge className="bg-green-100 text-green-800">Active</Badge>
                      ) : (
                        <Badge variant="secondary">Inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {format(new Date(agent.created_at), 'MMM d, yyyy')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
