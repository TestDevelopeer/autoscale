<?php

declare(strict_types=1);

namespace App\Orchid\Screens;

use App\Models\Organization;
use Orchid\Screen\Actions\Link;
use Orchid\Screen\Screen;
use Orchid\Screen\TD;
use Orchid\Support\Facades\Layout;

class OrganizationListScreen extends Screen
{
    public function query(): iterable
    {
        return ['organizations' => Organization::query()->orderBy('name')->get()];
    }

    public function name(): ?string
    {
        return 'Клиенты';
    }

    public function commandBar(): iterable
    {
        return [Link::make('Создать')->route('platform.organizations.create')];
    }

    public function layout(): iterable
    {
        return [
            Layout::table('organizations', [
                TD::make('name', 'Название'),
                TD::make('inn', 'ИНН'),
            ]),
        ];
    }
}
