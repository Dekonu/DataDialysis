'use client';

import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { api } from '@/lib/api';

interface ChangeHistoryExportButtonsProps {
  table_name?: string;
  change_type?: string;
}

export function ChangeHistoryExportButtons({
  table_name,
  change_type,
}: ChangeHistoryExportButtonsProps) {
  const handleExport = async (format: 'csv' | 'json') => {
    try {
      const blob = await api.changeHistory.export({
        format,
        table_name: table_name || undefined,
        change_type: change_type as 'INSERT' | 'UPDATE' | undefined,
      });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `change_history_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('csv')}
        className="flex items-center gap-2"
      >
        <Download className="h-4 w-4" />
        <span className="hidden sm:inline">Export CSV</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('json')}
        className="flex items-center gap-2"
      >
        <Download className="h-4 w-4" />
        <span className="hidden sm:inline">Export JSON</span>
      </Button>
    </div>
  );
}
