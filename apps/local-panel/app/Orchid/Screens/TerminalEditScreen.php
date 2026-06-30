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

class TerminalEditScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        return [
            'terminal' => [
                'name' => '',
                'driver_type' => 'demo',
                'config' => [],
            ],
        ];
    }

    public function name(): ?string
    {
        return 'Новый терминал';
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
                Input::make('terminal.name')->title('Название')->required(),
                Select::make('terminal.driver_type')->title('Тип')->options([
                    'demo' => 'DEMO',
                    'keli_d2008fa' => 'Keli D2008FA',
                    'cas_ci200a' => 'CAS CI-200A',
                ]),
                Input::make('terminal.config.port')->title('COM-порт')->help('Например COM3'),
            ]),
        ];
    }

    public function save(Request $request): \Illuminate\Http\RedirectResponse
    {
        $data = $request->get('terminal', []);
        try {
            $this->api->post('/api/terminals', [
                'name' => $data['name'],
                'driver_type' => $data['driver_type'],
                'config' => array_filter(['port' => $data['config']['port'] ?? null]),
            ]);
            Toast::success('Терминал создан');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }

        return redirect()->route('platform.terminals');
    }
}
