<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use Illuminate\Http\Request;
use Orchid\Screen\Actions\Button;
use Orchid\Screen\Fields\Input;
use Orchid\Screen\Fields\Select;
use Orchid\Screen\Screen;
use Orchid\Support\Facades\Layout;
use Orchid\Support\Facades\Toast;

class CameraEditScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        return ['camera' => ['name' => '', 'connection_type' => 'demo', 'alpr_provider' => 'demo']];
    }

    public function name(): ?string
    {
        return 'Новая камера';
    }

    public function commandBar(): iterable
    {
        return [Button::make('Сохранить')->method('save')->class('btn btn-primary')];
    }

    public function layout(): iterable
    {
        return [
            Layout::rows([
                Input::make('camera.name')->title('Название')->required(),
                Select::make('camera.connection_type')->title('Тип')->options([
                    'demo' => 'DEMO',
                    'http' => 'HTTP snapshot',
                    'rtsp' => 'RTSP',
                ]),
                Select::make('camera.alpr_provider')->title('ALPR provider')->options([
                    'demo' => 'Demo',
                    'mock' => 'Mock',
                ]),
            ]),
        ];
    }

    public function save(Request $request): \Illuminate\Http\RedirectResponse
    {
        $data = $request->get('camera', []);
        try {
            $this->api->post('/api/cameras', $data);
            Toast::success('Камера создана');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }

        return redirect()->route('platform.cameras');
    }
}
