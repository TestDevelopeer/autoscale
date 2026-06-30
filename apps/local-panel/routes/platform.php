<?php

declare(strict_types=1);

use App\Orchid\Screens\CameraEditScreen;
use App\Orchid\Screens\CameraListScreen;
use App\Orchid\Screens\DashboardScreen;
use App\Orchid\Screens\DiagnosticsScreen;
use App\Orchid\Screens\DriverEditScreen;
use App\Orchid\Screens\DriverListScreen;
use App\Orchid\Screens\LicenseScreen;
use App\Orchid\Screens\TerminalEditScreen;
use App\Orchid\Screens\TerminalListScreen;
use App\Orchid\Screens\User\UserProfileScreen;
use App\Orchid\Screens\WeighingJournalScreen;
use App\Orchid\Screens\WorkplaceEditScreen;
use App\Orchid\Screens\WorkplaceListScreen;
use App\Orchid\Screens\WorkplaceShowScreen;
use Illuminate\Support\Facades\Route;
use Tabuna\Breadcrumbs\Trail;

Route::screen('/main', DashboardScreen::class)->name('platform.main');

Route::screen('profile', UserProfileScreen::class)
    ->name('platform.profile')
    ->breadcrumbs(fn (Trail $trail) => $trail
        ->parent('platform.main')
        ->push(__('Profile'), route('platform.profile')));

Route::screen('terminals', TerminalListScreen::class)->name('platform.terminals');
Route::screen('terminals/create', TerminalEditScreen::class)->name('platform.terminals.create');

Route::screen('cameras', CameraListScreen::class)->name('platform.cameras');
Route::screen('cameras/create', CameraEditScreen::class)->name('platform.cameras.create');

Route::screen('workplaces', WorkplaceListScreen::class)->name('platform.workplaces');
Route::screen('workplaces/create', WorkplaceEditScreen::class)->name('platform.workplaces.create');
Route::screen('workplaces/{id}', WorkplaceShowScreen::class)->name('platform.workplaces.show');

Route::screen('weighings', WeighingJournalScreen::class)->name('platform.weighings');

Route::screen('drivers', DriverListScreen::class)->name('platform.drivers');
Route::screen('drivers/create', DriverEditScreen::class)->name('platform.drivers.create');

Route::screen('license', LicenseScreen::class)->name('platform.license');
Route::screen('diagnostics', DiagnosticsScreen::class)->name('platform.diagnostics');
