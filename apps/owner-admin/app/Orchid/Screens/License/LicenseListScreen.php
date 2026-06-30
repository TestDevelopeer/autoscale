<?php

declare(strict_types=1);

namespace App\Orchid\Screens\License;

use App\Models\License;
use App\Models\Organization;
use App\Services\LicenseSigningService;
use Orchid\Screen\Actions\Link;
use Orchid\Screen\Screen;
use Orchid\Screen\TD;
use Orchid\Support\Facades\Layout;

class LicenseListScreen extends Screen
{
    public function query(): iterable
    {
        return [
            'licenses' => License::query()->with('organization')->latest()->get(),
        ];
    }

    public function name(): ?string
    {
        return 'Лицензии';
    }

    public function commandBar(): iterable
    {
        return [Link::make('Создать')->route('platform.licenses.create')];
    }

    public function layout(): iterable
    {
        return [
            Layout::table('licenses', [
                TD::make('activation_code', 'Код'),
                TD::make('organization.name', 'Клиент'),
                TD::make('status', 'Статус'),
                TD::make('expires_at', 'Истекает'),
                TD::make('machine_fingerprint', 'Fingerprint')->width('200px'),
            ]),
        ];
    }
}
