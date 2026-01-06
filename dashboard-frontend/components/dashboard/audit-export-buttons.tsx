'use client';

import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

export function AuditExportButtons() {
  const handleExport = (format: 'json' | 'csv') => {
    window.open(`/api/audit-logs/export?format=${format}`, '_blank');
  };

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('json')}
      >
        <Download className="h-4 w-4 mr-2" />
        Export JSON
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('csv')}
      >
        <Download className="h-4 w-4 mr-2" />
        Export CSV
      </Button>
    </div>
  );
}

