<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use App\Support\OrchidRows;
use Orchid\Screen\Actions\Link;
use Orchid\Screen\Screen;
use Orchid\Screen\TD;
use Orchid\Support\Facades\Layout;

class WorkplaceListScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $workplaces = $this->api->get('/api/workplaces');
        } catch (\Throwable) {
            $workplaces = [];
        }

        return ['workplaces' => OrchidRows::fromArrays($workplaces)];
    }

    public function name(): ?string
    {
        return 'Рабочие места';
    }

    public function commandBar(): iterable
    {
        return [Link::make('Создать')->route('platform.workplaces.create')];
    }

    public function layout(): iterable
    {
        return [
            Layout::table('workplaces', [
                TD::make('name', 'Название'),
                TD::make('fsm_state', 'Состояние'),
                TD::make('is_running', 'Запущено')->render(fn ($w) => $w['is_running'] ? 'Да' : 'Нет'),
                TD::make('id', '')->render(fn ($w) => Link::make('Открыть')->route('platform.workplaces.show', $w['id'])),
            ]),
        ];
    }
}
