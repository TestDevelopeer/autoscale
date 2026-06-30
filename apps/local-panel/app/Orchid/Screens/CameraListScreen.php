<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use App\Support\OrchidRows;
use Orchid\Screen\Actions\Link;
use Orchid\Screen\Screen;
use Orchid\Screen\TD;
use Orchid\Support\Facades\Layout;

class CameraListScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $cameras = $this->api->get('/api/cameras');
        } catch (\Throwable) {
            $cameras = [];
        }

        return ['cameras' => OrchidRows::fromArrays($cameras)];
    }

    public function name(): ?string
    {
        return 'Камеры';
    }

    public function commandBar(): iterable
    {
        return [Link::make('Добавить')->route('platform.cameras.create')];
    }

    public function layout(): iterable
    {
        return [
            Layout::table('cameras', [
                TD::make('name', 'Название'),
                TD::make('connection_type', 'Тип'),
                TD::make('alpr_provider', 'ALPR'),
            ]),
        ];
    }
}
