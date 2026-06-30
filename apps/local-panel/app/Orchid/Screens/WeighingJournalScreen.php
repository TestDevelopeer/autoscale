<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use App\Support\AutoscaleLabels;
use App\Support\OrchidRows;
use Orchid\Screen\Screen;
use Orchid\Screen\Repository;
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

        return ['weighings' => OrchidRows::fromArrays($weighings)];
    }

    public function name(): ?string
    {
        return 'Журнал взвешивания';
    }

    public function layout(): iterable
    {
        return [
            Layout::table('weighings', [
                TD::make('recorded_at', 'Дата/время')->render(function (Repository $r) {
                    $ts = $r->get('recorded_at');
                    if (! $ts) {
                        return '—';
                    }

                    return date('d.m.Y H:i:s', strtotime((string) $ts));
                }),
                TD::make('plate_normalized', 'Номер')->render(fn (Repository $r) => $r->get('plate_normalized') ?? $r->get('plate_raw') ?? '—'),
                TD::make('weight', 'Вес')->render(function (Repository $r) {
                    if ($r->get('weight') === null) {
                        return '—';
                    }

                    return number_format((float) $r->get('weight'), 0, '.', ' ').' '.($r->get('unit') ?? 'кг');
                }),
                TD::make('stable', 'Стабильный')->render(fn (Repository $r) => $r->get('stable') ? 'Да' : 'Нет'),
                TD::make('workplace_name', 'Рабочее место'),
                TD::make('status', 'Статус')->render(fn (Repository $r) => AutoscaleLabels::weighingStatus($r->get('status'))),
            ]),
        ];
    }
}
