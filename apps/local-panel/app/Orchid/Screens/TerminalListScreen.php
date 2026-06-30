<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use Orchid\Screen\Actions\Link;
use Orchid\Screen\Screen;
use Orchid\Screen\TD;
use Orchid\Support\Facades\Layout;

class TerminalListScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $terminals = $this->api->get('/api/terminals');
        } catch (\Throwable) {
            $terminals = [];
        }

        return ['terminals' => $terminals];
    }

    public function name(): ?string
    {
        return 'Терминалы';
    }

    public function commandBar(): iterable
    {
        return [
            Link::make('Добавить')->route('platform.terminals.create'),
        ];
    }

    public function layout(): iterable
    {
        return [
            Layout::table('terminals', [
                TD::make('name', 'Название'),
                TD::make('driver_type', 'Тип'),
                TD::make('enabled', 'Вкл.')->render(fn ($t) => $t['enabled'] ? 'Да' : 'Нет'),
            ]),
        ];
    }
}
