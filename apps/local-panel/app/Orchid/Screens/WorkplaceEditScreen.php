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

class WorkplaceEditScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $terminals = $this->api->get('/api/terminals');
            $cameras = $this->api->get('/api/cameras');
        } catch (\Throwable) {
            $terminals = [];
            $cameras = [];
        }

        return [
            'workplace' => [
                'name' => '',
                'terminal_id' => $terminals[0]['id'] ?? null,
                'camera_ids' => isset($cameras[0]['id']) ? [$cameras[0]['id']] : [],
                'alpr_provider' => 'demo',
                'min_weight_threshold' => 100,
                'stable_seconds' => 2,
                'auto_confirm' => true,
            ],
            'terminals' => collect($terminals)->pluck('name', 'id')->toArray(),
            'cameras' => collect($cameras)->pluck('name', 'id')->toArray(),
        ];
    }

    public function name(): ?string
    {
        return 'Новое рабочее место';
    }

    public function commandBar(): iterable
    {
        return [
            Button::make('Сохранить')->method('save')->class('btn btn-primary'),
        ];
    }

    public function layout(): iterable
    {
        return [
            Layout::rows([
                Input::make('workplace.name')->title('Название')->required(),
                Select::make('workplace.terminal_id')->title('Терминал')->options('terminals')->required(),
                Select::make('workplace.camera_ids')->title('Камеры')->options('cameras')->multiple(),
                Select::make('workplace.alpr_provider')->title('ALPR')->options([
                    'demo' => 'DEMO',
                    'disabled' => 'Отключён',
                ]),
                Input::make('workplace.min_weight_threshold')->title('Мин. вес (кг)')->type('number'),
                Input::make('workplace.stable_seconds')->title('Стабилизация (сек)')->type('number'),
            ]),
        ];
    }

    public function save(Request $request): \Illuminate\Http\RedirectResponse
    {
        $data = $request->get('workplace', []);
        try {
            $this->api->post('/api/workplaces', [
                'name' => $data['name'],
                'terminal_id' => $data['terminal_id'],
                'camera_ids' => array_values(array_filter((array) ($data['camera_ids'] ?? []))),
                'alpr_provider' => $data['alpr_provider'] ?? 'demo',
                'min_weight_threshold' => (float) ($data['min_weight_threshold'] ?? 100),
                'stable_seconds' => (float) ($data['stable_seconds'] ?? 2),
                'auto_confirm' => filter_var($data['auto_confirm'] ?? true, FILTER_VALIDATE_BOOLEAN),
            ]);
            Toast::success('Рабочее место создано');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }

        return redirect()->route('platform.workplaces');
    }
}
