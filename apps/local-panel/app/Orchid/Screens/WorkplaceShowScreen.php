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

class WorkplaceShowScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        $id = request()->route('id');

        return [
            'workplace_id' => $id,
            'ws_url' => $this->api->wsUrl().'/ws/workplaces/'.$id,
        ];
    }

    public function name(): ?string
    {
        return 'Рабочее место';
    }

    public function commandBar(): iterable
    {
        return [
            Button::make('Старт')->method('start')->class('btn btn-success'),
            Button::make('Стоп')->method('stop')->class('btn btn-secondary'),
        ];
    }

    public function layout(): iterable
    {
        return [
            Layout::view('orchid.autoscale.workplace-live'),
        ];
    }

    public function start(Request $request): void
    {
        try {
            $this->api->post('/api/workplaces/'.$request->route('id').'/start');
            Toast::success('Workflow запущен');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }
    }

    public function stop(Request $request): void
    {
        try {
            $this->api->post('/api/workplaces/'.$request->route('id').'/stop');
            Toast::info('Остановлено');
        } catch (\Throwable $e) {
            Toast::error($e->getMessage());
        }
    }
}
