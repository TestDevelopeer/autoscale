<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use Orchid\Screen\Screen;
use Orchid\Support\Facades\Layout;

class DiagnosticsScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $health = $this->api->health();
        } catch (\Throwable $e) {
            $health = ['status' => 'error', 'message' => $e->getMessage()];
        }

        return [
            'health' => $health,
            'panel_version' => config('app.version', '0.1.0'),
            'api_url' => $this->api->baseUrl(),
        ];
    }

    public function name(): ?string
    {
        return 'Диагностика';
    }

    public function layout(): iterable
    {
        return [
            Layout::view('orchid.autoscale.diagnostics'),
        ];
    }
}
