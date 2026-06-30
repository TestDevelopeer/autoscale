@php
    use App\Support\AutoscaleLabels;
    $statusLabel = AutoscaleLabels::licenseStatus($license['status'] ?? null);
    $isValid = $license['valid'] ?? false;
@endphp

<dl class="row mb-0">
    <dt class="col-sm-3">Статус</dt>
    <dd class="col-sm-9">
        <span class="badge bg-{{ $isValid ? 'success' : 'secondary' }}">{{ $statusLabel }}</span>
    </dd>
    <dt class="col-sm-3">Сообщение</dt>
    <dd class="col-sm-9">{{ $license['user_message'] ?? '—' }}</dd>
    <dt class="col-sm-3">Организация</dt>
    <dd class="col-sm-9">{{ $license['organization_name'] ?? 'Demo Organization' }}</dd>
    <dt class="col-sm-3">Модули</dt>
    <dd class="col-sm-9">
        @foreach ($license['modules'] ?? [] as $module)
            <span class="badge bg-light text-dark border me-1">{{ $module }}</span>
        @endforeach
    </dd>
    <dt class="col-sm-3">Действует до</dt>
    <dd class="col-sm-9">
        @if (!empty($license['expires_at']))
            {{ date('d.m.Y H:i', strtotime($license['expires_at'])) }}
        @else
            —
        @endif
    </dd>
    <dt class="col-sm-3">Fingerprint</dt>
    <dd class="col-sm-9"><small class="text-muted user-select-all">{{ $license['machine_fingerprint'] ?? '—' }}</small></dd>
</dl>
