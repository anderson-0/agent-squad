'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { useAuthStore } from '@/lib/store/auth';
import { squadsAPI } from '@/lib/api/squads';
import { Squad } from '@/lib/api/types';

// Dynamic imports for code splitting (lazy load dialogs)
const CreateSquadDialog = dynamic(
  () => import('@/components/squads/CreateSquadDialog').then((mod) => ({ default: mod.CreateSquadDialog })),
  { ssr: false }
);
const DeleteSquadDialog = dynamic(
  () => import('@/components/squads/DeleteSquadDialog').then((mod) => ({ default: mod.DeleteSquadDialog })),
  { ssr: false }
);
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Users, Eye, Edit } from 'lucide-react';
import { format } from 'date-fns';

export default function SquadsPage() {
  const user = useAuthStore((state) => state.user);
  const [squads, setSquads] = useState<Squad[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalSquads, setTotalSquads] = useState(0);

  const fetchSquads = async () => {
    if (!user?.organization_id) return;

    try {
      setIsLoading(true);
      const data = await squadsAPI.listSquads(user.organization_id, 1, 50);
      setSquads(data.items);
      setTotalSquads(data.total);
    } catch (error) {
      console.error('Failed to fetch squads:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSquads();
  }, [user]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Squads</h1>
          <p className="text-muted-foreground mt-1">
            Manage your AI agent squads
          </p>
        </div>
        <CreateSquadDialog onSuccess={fetchSquads} />
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Squads</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalSquads}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Active squads in your organization
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Squads</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {squads.filter((s) => s.is_active).length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Currently active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {squads.reduce((acc, s) => acc + (s.agent_count || 0), 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Across all squads
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Squads Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Squads</CardTitle>
          <CardDescription>
            View and manage all squads in your organization
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : squads.length === 0 ? (
            <div className="text-center py-12">
              <Users className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-semibold">No squads yet</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Get started by creating your first squad
              </p>
              <div className="mt-6">
                <CreateSquadDialog onSuccess={fetchSquads} />
              </div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Agents</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {squads.map((squad) => (
                  <TableRow key={squad.id}>
                    <TableCell>
                      <div>
                        <Link
                          href={`/squads/${squad.id}`}
                          className="font-medium hover:underline"
                        >
                          {squad.name}
                        </Link>
                        {squad.description && (
                          <p className="text-sm text-muted-foreground truncate max-w-xs">
                            {squad.description}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{squad.squad_type}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>{squad.agent_count || 0}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {squad.is_active ? (
                        <Badge className="bg-green-100 text-green-800">Active</Badge>
                      ) : (
                        <Badge variant="secondary">Inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {format(new Date(squad.created_at), 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link href={`/squads/${squad.id}`}>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                        <DeleteSquadDialog
                          squadId={squad.id}
                          squadName={squad.name}
                          onSuccess={fetchSquads}
                          trigger={
                            <Button variant="ghost" size="sm">
                              <Edit className="h-4 w-4" />
                            </Button>
                          }
                        />
                      </div>
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
