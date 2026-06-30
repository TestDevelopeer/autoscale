<?php

namespace Database\Seeders;

use App\Models\License;
use App\Models\Organization;
use App\Services\LicenseSigningService;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $org = Organization::query()->firstOrCreate(
            ['name' => 'Demo Organization'],
            ['inn' => '7700000000'],
        );

        License::query()->firstOrCreate(
            ['organization_id' => $org->id, 'activation_code' => 'DEMO-DEMO'],
            [
                'status' => 'active',
                'modules' => [
                    'core', 'terminals', 'cameras', 'alpr', 'weighing_journal',
                    'drivers_registry', 'workplaces', 'reports_basic', 'api_access', 'multi_workplace',
                ],
                'limits' => [
                    'max_users' => 10,
                    'max_workplaces' => 5,
                    'max_terminals' => 10,
                    'max_cameras' => 20,
                    'max_records_per_month' => 0,
                ],
                'expires_at' => now()->addYear(),
                'grace_days' => 14,
                'offline_until' => now()->addMonths(6),
            ],
        );
    }
}
