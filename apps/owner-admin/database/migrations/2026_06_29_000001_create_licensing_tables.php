<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('organizations', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('name');
            $table->string('inn')->nullable();
            $table->text('comment')->nullable();
            $table->timestamps();
        });

        Schema::create('license_modules', function (Blueprint $table) {
            $table->id();
            $table->string('key')->unique();
            $table->string('name');
            $table->text('description')->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('licenses', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('organization_id')->constrained('organizations')->cascadeOnDelete();
            $table->string('activation_code')->unique();
            $table->string('status')->default('active');
            $table->json('modules');
            $table->json('limits');
            $table->timestampTz('expires_at');
            $table->unsignedInteger('grace_days')->default(14);
            $table->timestampTz('offline_until')->nullable();
            $table->string('machine_fingerprint')->nullable();
            $table->string('status_reason')->nullable();
            $table->timestampTz('status_changed_at')->nullable();
            $table->timestamps();
        });

        Schema::create('license_activations', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('license_id')->constrained('licenses')->cascadeOnDelete();
            $table->string('machine_fingerprint');
            $table->string('hostname')->nullable();
            $table->string('product_version')->nullable();
            $table->timestampTz('activated_at');
            $table->timestamps();
        });

        Schema::create('offline_activation_requests', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('license_id')->nullable()->constrained('licenses')->nullOnDelete();
            $table->json('request_payload');
            $table->string('machine_fingerprint');
            $table->string('status')->default('pending');
            $table->timestamps();
        });

        Schema::create('issued_license_files', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('license_id')->constrained('licenses')->cascadeOnDelete();
            $table->json('signed_payload');
            $table->string('machine_fingerprint');
            $table->foreignId('issued_by')->nullable()->constrained('users')->nullOnDelete();
            $table->timestamps();
        });

        Schema::create('audit_log', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignId('user_id')->nullable()->constrained('users')->nullOnDelete();
            $table->string('action');
            $table->string('entity_type')->nullable();
            $table->uuid('entity_id')->nullable();
            $table->json('details')->nullable();
            $table->timestampTz('created_at')->useCurrent();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('audit_log');
        Schema::dropIfExists('issued_license_files');
        Schema::dropIfExists('offline_activation_requests');
        Schema::dropIfExists('license_activations');
        Schema::dropIfExists('licenses');
        Schema::dropIfExists('license_modules');
        Schema::dropIfExists('organizations');
    }
};
