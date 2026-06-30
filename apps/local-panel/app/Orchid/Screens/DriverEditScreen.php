<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use Illuminate\Http\Request;
use Orchid\Screen\Actions\Button;
use Orchid\Screen\Fields\Input;
use Orchid\Screen\Screen;
use Orchid\Support\Facades\Layout;
use Orchid\Support\Facades\Toast;

class DriverEditScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        return ['driver' => ['full_name' => '', 'plate_raw' => '', 'phone' => '', 'organization' => '']];
    }

    public function name(): ?string
    {
        return 'Новая карточка';
    }

    public function commandBar(): iterable
    {
        return [Button::make('Сохранить')->method('save')->class('btn btn-primary')];
    }

    public function layout(): iterable
    {
        return [
            Layout::rows([
                Input::make('driver.plate_raw')->title('Госномер')->required(),
                Input::make('driver.full_name')->title('ФИО водителя')->required(),
                Input::make('driver.phone')->title('Телефон'),
                Input::make('driver.organization')->title('Организация'),
            ]),
        ];
    }

    public function save(Request $request): \Illuminate\Http\RedirectResponse
    {
        try {
            $this->api->post('/api/drivers', $request->get('driver', []));
            Toast::success('Карточка создана');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }

        return redirect()->route('platform.drivers');
    }
}
