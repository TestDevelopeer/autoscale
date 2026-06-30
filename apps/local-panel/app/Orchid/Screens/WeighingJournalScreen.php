<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use App\Support\AutoscaleLabels;
use Orchid\Screen\Screen;
use Orchid\Screen\TD;
use Orchid\Support\Facades\Layout;

class WeighingJournalScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $weighings = $this->api->get('/api/weighings');
            $workplaceNames = collect($this->api->get('/api/workplaces'))->pluck('name', 'id')->all();
            $weighings = array_map(
                fn (array $row) => array_merge($row, [
                    'workplace_name' => $workplaceNames[$row['workplace_id'] ?? ''] ?? '—',
                ]),
                $weighings
            );
        } catch (\Throwable) {
            $weighings = [];
        }

        return ['weighings' => $weighings];
    }

    public function name(): ?string
    {
        return 'Журнал взвешивания';
    }

    public function layout(): iterable
    {
        return [
            Layout::table('weighings', [
                TD::make('recorded_at', 'Дата/время')->render(function (array $r) {
                    $ts = $r['recorded_at'] ?? null;
                    if (! $ts) {
                        return '—';
                    }

                    return date('d.m.Y H:i:s', strtotime($ts));
                }),
                TD::make('plate_normalized', 'Номер')->render(fn (array $r) => $r['plate_normalized'] ?? $r['plate_raw'] ?? '—'),
                TD::make('weight', 'Вес')->render(function (array $r) {
                    if (! isset($r['weight'])) {
                        return '—';
                    }

                    return number_format((float) $r['weight'], 0, '.', ' ').' '.($r['unit'] ?? 'кг');
                }),
                TD::make('stable', 'Стабильный')->render(fn (array $r) => ($r['stable'] ?? false) ? 'Да' : 'Нет'),
                TD::make('workplace_name', 'Рабочее место'),
                TD::make('status', 'Статус')->render(fn (array $r) => AutoscaleLabels::weighingStatus($r['status'] ?? null)),
            ]),
        ];
    }
}
