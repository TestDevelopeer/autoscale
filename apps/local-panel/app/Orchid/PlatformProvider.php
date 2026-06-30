<?php

declare(strict_types=1);

namespace App\Orchid;

use Orchid\Platform\Dashboard;
use Orchid\Platform\ItemPermission;
use Orchid\Platform\OrchidServiceProvider;
use Orchid\Screen\Actions\Menu;
use Orchid\Support\Color;

class PlatformProvider extends OrchidServiceProvider
{
    public function boot(Dashboard $dashboard): void
    {
        parent::boot($dashboard);
    }

    public function menu(): array
    {
        return [
            Menu::make('Dashboard')
                ->icon('bs.speedometer2')
                ->route('platform.main')
                ->title('Autoscale'),

            Menu::make('Терминалы')
                ->icon('bs.cpu')
                ->route('platform.terminals'),

            Menu::make('Камеры')
                ->icon('bs.camera-video')
                ->route('platform.cameras'),

            Menu::make('Рабочие места')
                ->icon('bs.geo-alt')
                ->route('platform.workplaces'),

            Menu::make('Журнал взвешивания')
                ->icon('bs.journal-text')
                ->route('platform.weighings'),

            Menu::make('Водители / ТС')
                ->icon('bs.person-vcard')
                ->route('platform.drivers')
                ->divider(),

            Menu::make('Лицензия')
                ->icon('bs.key')
                ->route('platform.license'),

            Menu::make('Диагностика')
                ->icon('bs.heart-pulse')
                ->route('platform.diagnostics'),
        ];
    }

    public function permissions(): array
    {
        return [
            ItemPermission::group('Autoscale')
                ->addPermission('platform.index', 'Доступ к панели Orchid')
                ->addPermission('platform.autoscale', 'Доступ к Autoscale'),
        ];
    }
}
