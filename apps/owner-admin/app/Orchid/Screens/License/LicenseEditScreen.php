<?php

declare(strict_types=1);

namespace App\Orchid\Screens\License;

use App\Models\License;
use App\Models\Organization;
use App\Services\LicenseSigningService;
use Illuminate\Http\Request;
use Orchid\Screen\Actions\Button;
use Orchid\Screen\Fields\Input;
use Orchid\Screen\Fields\Relation;
use Orchid\Screen\Screen;
use Orchid\Support\Facades\Layout;
use Orchid\Support\Facades\Toast;

class LicenseEditScreen extends Screen
{
    public function query(?License $license = null): iterable
    {
        return ['license' => $license ?? new License([
            'modules' => ['core', 'terminals', 'cameras', 'alpr', 'workplaces', 'weighing_journal', 'drivers_registry'],
            'limits' => ['max_users' => 5, 'max_workplaces' => 2, 'max_terminals' => 4, 'max_cameras' => 8],
            'grace_days' => 14,
            'status' => 'active',
        ])];
    }

    public function name(): ?string
    {
        return 'Лицензия';
    }

    public function commandBar(): iterable
    {
        return [Button::make('Сохранить')->method('save')->class('btn btn-primary')];
    }

    public function layout(): iterable
    {
        return [
            Layout::rows([
                Relation::make('license.organization_id')->title('Клиент')->fromModel(Organization::class, 'name'),
                Input::make('license.expires_at')->type('datetime-local')->title('Срок действия'),
                Input::make('license.grace_days')->type('number')->title('Grace days'),
            ]),
        ];
    }

    public function save(Request $request, LicenseSigningService $signing): void
    {
        $data = $request->get('license', []);
        $license = License::query()->find($request->route('license')) ?? new License;
        $license->fill([
            'organization_id' => $data['organization_id'],
            'expires_at' => $data['expires_at'],
            'grace_days' => $data['grace_days'] ?? 14,
            'modules' => $license->modules ?? ['core', 'terminals', 'cameras', 'alpr', 'workplaces', 'weighing_journal', 'drivers_registry'],
            'limits' => $license->limits ?? ['max_users' => 5, 'max_workplaces' => 2, 'max_terminals' => 4, 'max_cameras' => 8],
            'status' => 'active',
        ]);
        if (! $license->activation_code) {
            $license->activation_code = LicenseSigningService::generateActivationCode();
        }
        $license->save();
        Toast::success('Лицензия сохранена: '.$license->activation_code);
    }
}
