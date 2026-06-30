<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Services\LocalApiClient;
use Orchid\Screen\Actions\Button;
use Orchid\Screen\Fields\Input;
use Orchid\Screen\Screen;
use Orchid\Support\Facades\Layout;
use Orchid\Support\Facades\Toast;

class DashboardScreen extends Screen
{
    public function __construct(private readonly LocalApiClient $api) {}

    public function query(): iterable
    {
        try {
            $health = $this->api->health();
            $license = $this->api->licenseStatus();
        } catch (\Throwable $e) {
            $health = ['status' => 'error', 'message' => $e->getMessage()];
            $license = ['valid' => false, 'user_message' => 'local-api недоступен'];
        }

        return compact('health', 'license');
    }

    public function name(): ?string
    {
        return 'Dashboard';
    }

    public function commandBar(): iterable
    {
        return [];
    }

    public function layout(): iterable
    {
        return [
            Layout::view('orchid.autoscale.dashboard'),
        ];
    }
}
