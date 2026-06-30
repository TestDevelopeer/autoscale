<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use Orchid\Screen\Actions\Link;
use Orchid\Screen\Screen;
use Orchid\Screen\TD;
use Orchid\Support\Facades\Layout;

class DriverListScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $drivers = $this->api->get('/api/drivers');
        } catch (\Throwable) {
            $drivers = [];
        }

        return ['drivers' => $drivers];
    }

    public function name(): ?string
    {
        return 'Водители / Автомобили';
    }

    public function commandBar(): iterable
    {
        return [Link::make('Создать')->route('platform.drivers.create')];
    }

    public function layout(): iterable
    {
        return [
            Layout::table('drivers', [
                TD::make('full_name', 'ФИО'),
                TD::make('plate_normalized', 'Номер'),
                TD::make('phone', 'Телефон'),
                TD::make('organization', 'Организация'),
            ]),
        ];
    }
}
