'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { TimeRange } from '@/types/api';

const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '1h', label: 'Last Hour' },
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
];

export interface TimeRangeSelectorProps {
  defaultValue?: TimeRange;
  paramName?: string;
  onValueChange?: (value: TimeRange) => void;
}

export function TimeRangeSelector({
  defaultValue = '24h',
  paramName = 'timeRange',
  onValueChange,
}: TimeRangeSelectorProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentValue = (searchParams.get(paramName) as TimeRange) || defaultValue;

  const handleValueChange = (value: TimeRange) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set(paramName, value);
    router.push(`?${params.toString()}`, { scroll: false });
    onValueChange?.(value);
  };

  return (
    <Select value={currentValue} onValueChange={handleValueChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select time range" />
      </SelectTrigger>
      <SelectContent>
        {TIME_RANGE_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

