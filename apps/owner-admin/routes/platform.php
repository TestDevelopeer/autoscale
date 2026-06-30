<?php

declare(strict_types=1);

use App\Orchid\Screens\License\LicenseEditScreen;
use App\Orchid\Screens\License\LicenseListScreen;
use App\Orchid\Screens\OrganizationEditScreen;
use App\Orchid\Screens\OrganizationListScreen;
use App\Orchid\Screens\PlatformScreen;
use Illuminate\Support\Facades\Route;

Route::screen('/main', PlatformScreen::class)->name('platform.main');

Route::screen('organizations', OrganizationListScreen::class)->name('platform.organizations');
Route::screen('organizations/create', OrganizationEditScreen::class)->name('platform.organizations.create');

Route::screen('licenses', LicenseListScreen::class)->name('platform.licenses');
Route::screen('licenses/create', LicenseEditScreen::class)->name('platform.licenses.create');
