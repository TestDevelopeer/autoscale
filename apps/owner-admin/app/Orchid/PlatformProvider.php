<?php

declare(strict_types=1);

namespace App\Orchid;

use App\Orchid\Screens\License\LicenseEditScreen;
use App\Orchid\Screens\License\LicenseListScreen;
use App\Orchid\Screens\OrganizationEditScreen;
use App\Orchid\Screens\OrganizationListScreen;
use Orchid\Platform\Dashboard;
use Orchid\Platform\OrchidServiceProvider;
use Orchid\Screen\Actions\Menu;

class PlatformProvider extends OrchidServiceProvider
{
    public function boot(Dashboard $dashboard): void
    {
        parent::boot($dashboard);
    }

    public function menu(): array
    {
        return [
            Menu::make('Клиенты')->icon('bs.building')->route('platform.organizations'),
            Menu::make('Лицензии')->icon('bs.key')->route('platform.licenses'),
        ];
    }
}
