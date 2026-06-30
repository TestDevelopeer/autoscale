<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Models\Organization;
use Illuminate\Http\Request;
use Orchid\Screen\Actions\Button;
use Orchid\Screen\Fields\Input;
use Orchid\Screen\Screen;
use Orchid\Support\Facades\Layout;
use Orchid\Support\Facades\Toast;

class OrganizationEditScreen extends Screen
{
    public function query(): iterable
    {
        return ['organization' => new Organization];
    }

    public function name(): ?string
    {
        return 'Новый клиент';
    }

    public function commandBar(): iterable
    {
        return [Button::make('Сохранить')->method('save')->class('btn btn-primary')];
    }

    public function layout(): iterable
    {
        return [
            Layout::rows([
                Input::make('organization.name')->title('Название')->required(),
                Input::make('organization.inn')->title('ИНН'),
            ]),
        ];
    }

    public function save(Request $request): \Illuminate\Http\RedirectResponse
    {
        Organization::query()->create($request->get('organization', []));
        Toast::success('Клиент создан');

        return redirect()->route('platform.organizations');
    }
}
