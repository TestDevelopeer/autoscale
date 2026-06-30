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

class LicenseScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $license = $this->api->licenseStatus();
        } catch (\Throwable $e) {
            $license = ['valid' => false, 'user_message' => $e->getMessage()];
        }

        return ['license' => $license];
    }

    public function name(): ?string
    {
        return 'Лицензия';
    }

    public function commandBar(): iterable
    {
        return [
            Button::make('Запрос offline-активации')
                ->method('downloadRequest'),
        ];
    }

    public function layout(): iterable
    {
        return [
            Layout::rows([
                Input::make('license_id')->title('ID лицензии')->help('Для online activation'),
                Input::make('activation_code')->title('Код активации'),
            ]),
            Layout::view('orchid.autoscale.license'),
            Layout::rows([
                Button::make('Online activation')->method('activateOnline')->class('btn btn-primary'),
            ]),
        ];
    }

    public function activateOnline(Request $request): void
    {
        try {
            $this->api->post('/api/license/activate-online', [
                'license_id' => $request->get('license_id'),
                'activation_code' => $request->get('activation_code'),
            ]);
            Toast::success('Лицензия активирована');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }
    }

    public function downloadRequest(): void
    {
        try {
            $data = $this->api->post('/api/license/offline/request');
            session(['offline_request' => $data]);
            Toast::info('Запрос создан — скопируйте fingerprint');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }
    }
}
