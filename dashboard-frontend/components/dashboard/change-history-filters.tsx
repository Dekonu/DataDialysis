'use client';

import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Filter, X } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';

export function ChangeHistoryFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [tableName, setTableName] = useState(searchParams.get('table_name') || '');
  const [recordId, setRecordId] = useState(searchParams.get('record_id') || '');
  const [fieldName, setFieldName] = useState(searchParams.get('field_name') || '');
  const [changeType, setChangeType] = useState(searchParams.get('change_type') || '');

  const applyFilters = () => {
    const params = new URLSearchParams();
    
    if (tableName) params.set('table_name', tableName);
    if (recordId) params.set('record_id', recordId);
    if (fieldName) params.set('field_name', fieldName);
    if (changeType) params.set('change_type', changeType);
    
    // Preserve other params
    const timeRange = searchParams.get('timeRange');
    if (timeRange) params.set('timeRange', timeRange);
    
    router.push(`/change-history?${params.toString()}`);
  };

  const clearFilters = () => {
    setTableName('');
    setRecordId('');
    setFieldName('');
    setChangeType('');
    
    const params = new URLSearchParams();
    const timeRange = searchParams.get('timeRange');
    if (timeRange) params.set('timeRange', timeRange);
    
    router.push(`/change-history?${params.toString()}`);
  };

  const hasActiveFilters = tableName || recordId || fieldName || changeType;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Filters
            </CardTitle>
            <CardDescription>Filter change history by various criteria</CardDescription>
          </div>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-2" />
              Clear
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-2">
            <Label htmlFor="table_name">Table Name</Label>
            <Select value={tableName || 'all'} onValueChange={(value) => setTableName(value === 'all' ? '' : value)}>
              <SelectTrigger id="table_name">
                <SelectValue placeholder="All tables" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All tables</SelectItem>
                <SelectItem value="patients">Patients</SelectItem>
                <SelectItem value="encounters">Encounters</SelectItem>
                <SelectItem value="observations">Observations</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="record_id">Record ID</Label>
            <Input
              id="record_id"
              placeholder="Filter by record ID"
              value={recordId}
              onChange={(e) => setRecordId(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="field_name">Field Name</Label>
            <Input
              id="field_name"
              placeholder="Filter by field name"
              value={fieldName}
              onChange={(e) => setFieldName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="change_type">Change Type</Label>
            <Select value={changeType || 'all'} onValueChange={(value) => setChangeType(value === 'all' ? '' : value)}>
              <SelectTrigger id="change_type">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                <SelectItem value="INSERT">INSERT</SelectItem>
                <SelectItem value="UPDATE">UPDATE</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <Button onClick={applyFilters}>Apply Filters</Button>
        </div>
      </CardContent>
    </Card>
  );
}
